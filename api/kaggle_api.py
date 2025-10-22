import argparse
import json
import os
from pathlib import Path
from kaggle.api.kaggle_api_extended import KaggleApi
from kagglesdk.models.types.model_api_service import ApiListModelsRequest
import csv


def list_models_and_save(
	page_size: int = 20,
	max_pages: int = 5,
	output_file: str | None = None,
	filter_keywords: list[str] | None = None,
	output_dir: str = 'api_output',
) -> None:
	api = KaggleApi()

	# Check for credentials: either ~/.kaggle/kaggle.json or env vars must be present
	kaggle_json = Path(os.path.expanduser('~')) / '.kaggle' / 'kaggle.json'
	has_env = bool(os.getenv('KAGGLE_USERNAME') and os.getenv('KAGGLE_KEY'))
	if not kaggle_json.exists() and not has_env:
		print("Could not find Kaggle credentials.")
		print(f"Expected to find: {kaggle_json}")
		print("Or set environment variables KAGGLE_USERNAME and KAGGLE_KEY.")
		print("See: https://github.com/Kaggle/kaggle-api#api-credentials")
		return

	try:
		api.authenticate()
	except Exception as e:
		print("Failed to authenticate with Kaggle API:", e)
		return

	next_page_token = None
	all_models = []
	page = 0

	while page < max_pages:
		page += 1
		# Use the lower-level kagglesdk client so we can read next_page_token from the response
		with api.build_kaggle_client() as kaggle:
			request = ApiListModelsRequest()
			request.page_size = page_size
			request.page_token = next_page_token or ''
			response = kaggle.models.model_api_client.list_models(request)

		models = getattr(response, 'models', []) or []
		token = getattr(response, 'next_page_token', None)

		print(f"Page {page}: {len(models)} models, Next Page Token = {token}")
		# convert model protobuf objects to dicts (simple mapping)
		for m in models:
			try:
				jm = m.to_json(m)
				# to_json may return a JSON string or a dict-like object
				if isinstance(jm, str):
					try:
						mdict = json.loads(jm)
					except Exception:
						# fallback to string wrapper
						mdict = {'raw': jm}
				else:
					mdict = jm
				all_models.append(mdict)
			except Exception:
				# fallback: basic attrs
				all_models.append({k: getattr(m, k, None) for k in ('id', 'ref', 'title', 'subtitle', 'author')})

		if not token:
			break
		next_page_token = token

	# Apply optional filtering on collected models
	if filter_keywords:
		lowered = [k.lower() for k in filter_keywords]
		def matches(m: dict) -> bool:
			joined = ' '.join(str(m.get(x, '') or '') for x in ('title', 'subtitle', 'description', 'ref'))
			joined = joined.lower()
			return any(k in joined for k in lowered)

		before = len(all_models)
		all_models = [m for m in all_models if matches(m)]
		print(f"Filtered models: {len(all_models)} of {before} match keywords {filter_keywords}")

	if output_file:
		# Ensure output directory exists
		output_path = Path(output_dir)
		output_path.mkdir(parents=True, exist_ok=True)

		# Construct full output file path
		full_output_path = output_path / output_file

		# Pretty-print JSON with indentation for readability
		with open(full_output_path, 'w', encoding='utf-8') as f:
			json.dump({'models': all_models}, f, ensure_ascii=False, indent=2)
		print(f"Saved {len(all_models)} model entries to {full_output_path}")


def parse_kaggle_model_url(url: str) -> tuple[str, str] | None:
	"""Parse Kaggle model URL like https://www.kaggle.com/models/<owner>/<slug>

	Returns (owner, slug) or None if parsing fails.
	"""
	try:
		# Remove query and fragment
		url = url.split('?')[0].split('#')[0]
		parts = url.split('://')[-1].split('/')
		# parts example: ['www.kaggle.com', 'models', 'qwen-lm', 'qwen3-next-80b']
		if 'models' in parts:
			i = parts.index('models')
			owner = parts[i + 1]
			slug = parts[i + 2]
			return owner, slug
	except Exception:
		return None


def fetch_models_from_csv(input_csv: str, output_file: str | None = None, output_dir: str = 'api_output') -> None:
	"""Read CSV with columns name,kaggle_url and fetch model metadata for each URL.

	Saves per-model JSON files into `output_dir/models_metadata` and a combined pretty JSON to `output_file` if provided.
	"""
	api = KaggleApi()

	# Credential check
	kaggle_json = Path(os.path.expanduser('~')) / '.kaggle' / 'kaggle.json'
	has_env = bool(os.getenv('KAGGLE_USERNAME') and os.getenv('KAGGLE_KEY'))
	if not kaggle_json.exists() and not has_env:
		print("Could not find Kaggle credentials.")
		print(f"Expected to find: {kaggle_json}")
		print("Or set environment variables KAGGLE_USERNAME and KAGGLE_KEY.")
		print("See: https://github.com/Kaggle/kaggle-api#api-credentials")
		return

	try:
		api.authenticate()
	except Exception as e:
		print("Failed to authenticate with Kaggle API:", e)
		return

	# Create output directories
	base_output_dir = Path(output_dir)
	base_output_dir.mkdir(parents=True, exist_ok=True)

	models_metadata_dir = base_output_dir / 'models_metadata'
	models_metadata_dir.mkdir(parents=True, exist_ok=True)

	combined = []
	with open(input_csv, newline='', encoding='utf-8') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			name = row.get('name') or row.get('Name') or ''
			url = row.get('kaggle_url') or row.get('url') or row.get('Kaggle URL')
			if not url:
				print(f"Skipping row with no URL: {row}")
				continue
			parsed = parse_kaggle_model_url(url)
			if not parsed:
				print(f"Could not parse model URL: {url}")
				continue
			owner, slug = parsed
			model_ref = f"{owner}/{slug}"
			print(f"Fetching metadata for {model_ref} ({name})")
			try:
				model = api.model_get(model_ref)
			except Exception as e:
				print(f"Failed to get model {model_ref}: {e}")
				combined.append({'input_name': name, 'ref': model_ref, 'error': str(e)})
				continue

			# Convert the SDK model object (which may contain nested objects) into a plain dict
			def model_to_dict(m) -> dict:
				# Try SDK-provided to_json first
				try:
					jm = None
					# Some SDK objects provide a to_json function or method
					if hasattr(m, 'to_json'):
						jm = m.to_json(m)
					if isinstance(jm, str):
						try:
							return json.loads(jm)
						except Exception:
							# fallback to manual dict
							pass
				except Exception:
					pass

				# Manual conversion: iterate known attributes and convert nested lists/objects
				out = {}
				for attr in ('id', 'ref', 'title', 'subtitle', 'author', 'slug', 'description', 'is_private', 'publish_time', 'provenanceSources', 'url', 'publishTime', 'provenance_sources'):
					val = getattr(m, attr, None)
					if val is not None:
						out[attr] = val

				# Instances: may be a list of SDK objects
				instances = getattr(m, 'instances', None)
				if instances:
					out['instances'] = []
					for ins in instances:
						ins_dict = {}
						for k in ('id', 'slug', 'framework', 'fineTunable', 'overview', 'usage', 'downloadUrl', 'versionId', 'versionNumber', 'url', 'licenseName', 'modelInstanceType', 'totalUncompressedBytes', 'externalBaseModelUrl', 'trainingData'):
							v = getattr(ins, k, None)
							if v is not None:
								ins_dict[k] = v
						# Some instance fields may be lists (trainingData)
						# If ins has attributes that are protobuf lists, they are iterable
						# Add the instance dict
						out['instances'].append(ins_dict)

				# Tags: convert tag objects to dicts
				tags = getattr(m, 'tags', None)
				if tags:
					out['tags'] = []
					for t in tags:
						try:
							# tag objects can often be dict-like or have attributes
							if isinstance(t, dict):
								out['tags'].append(t)
							else:
								out['tags'].append({
									'ref': getattr(t, 'ref', None),
									'name': getattr(t, 'name', None),
									'description': getattr(t, 'description', None),
									'fullPath': getattr(t, 'fullPath', None),
									'competitionCount': getattr(t, 'competitionCount', None),
									'datasetCount': getattr(t, 'datasetCount', None),
									'scriptCount': getattr(t, 'scriptCount', None),
									'totalCount': getattr(t, 'totalCount', None),
								})
						except Exception:
							pass

				# provenanceSources / provenanceSources may be an attribute
				prov = getattr(m, 'provenanceSources', None) or getattr(m, 'provenance_sources', None)
				if prov:
					out['provenanceSources'] = prov

				# Fallback: include any public __dict__ entries if available
				if hasattr(m, '__dict__'):
					for k, v in vars(m).items():
						if k not in out and not k.startswith('_'):
							out[k] = v

				return out

			full_md = model_to_dict(model)
			# Attach CSV input info
			full_md['input_name'] = name
			full_md['owner'] = owner
			full_md['slug'] = slug

			# Save per-model JSON file (complete structure)
			safe_name = f"{owner}__{slug}.json"
			with open(models_metadata_dir / safe_name, 'w', encoding='utf-8') as f:
				json.dump(full_md, f, ensure_ascii=False, indent=2)

			combined.append(full_md)

	if output_file:
		full_output_path = base_output_dir / output_file
		with open(full_output_path, 'w', encoding='utf-8') as f:
			json.dump({'models': combined}, f, ensure_ascii=False, indent=2)
		print(f"Saved combined metadata for {len(combined)} entries to {full_output_path}")



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='List Kaggle models and save metadata to JSON')
	parser.add_argument('--page-size', type=int, default=20, help='Number of models per page (default 20)')
	parser.add_argument('--max-pages', type=int, default=5, help='Max number of pages to fetch (default 5)')
	parser.add_argument('--output', type=str, default='kaggle_models.json', help='Output JSON filename')
	parser.add_argument('--filter', type=str, nargs='*', help='Filter keywords (e.g. llm transformer causal)')
	parser.add_argument('--input-csv', type=str, help='CSV file with name,kaggle_url rows to fetch specific models')
	parser.add_argument('--input-json', type=str, help='JSON file or glob pattern with kaggle_links output (e.g. output/kaggle_links_*.json)')
	parser.add_argument('--output-dir', type=str, default='api_output', help='Directory to save API output files')

	args = parser.parse_args()

	if args.input_csv:
		fetch_models_from_csv(args.input_csv, output_file=args.output, output_dir=args.output_dir)
	elif args.input_json:
		# If a glob pattern is provided, pick the most recent matching file
		import glob
		import os
		pattern = args.input_json
		matches = glob.glob(pattern)
		if not matches:
			# Try relative to /app if running in container
			matches = glob.glob(os.path.join('/app', pattern.lstrip('/')))
		if not matches:
			print(f'No matching JSON files for pattern: {pattern}')
		else:
			latest = max(matches, key=os.path.getctime)
			print(f'Using input JSON: {latest}')
			# Read JSON and write a temporary CSV that fetch_models_from_csv can consume
			import json
			from pathlib import Path
			with open(latest, 'r', encoding='utf-8') as jf:
				try:
					data = json.load(jf)
				except Exception as e:
					print(f'Failed to load JSON {latest}: {e}')
					data = None
			if data:
				# Normalize data to rows with name and kaggle_url
				rows = []
				if isinstance(data, dict) and 'models' in data and isinstance(data['models'], list):
					for m in data['models']:
						name = m.get('name') or m.get('title') or ''
						url = m.get('kaggle_url') or m.get('url') or m.get('ref') or m.get('kaggleUrl') or ''
						# If 'ref' is of form owner/slug, construct URL
						if url and isinstance(url, str) and url.count('/') == 1 and not url.startswith('http'):
							url = f'https://www.kaggle.com/models/{url}'
						rows.append({'name': name, 'kaggle_url': url})
				elif isinstance(data, list):
					for m in data:
						name = m.get('name') or m.get('title') or ''
						url = m.get('kaggle_url') or m.get('url') or m.get('ref') or ''
						if url and isinstance(url, str) and url.count('/') == 1 and not url.startswith('http'):
							url = f'https://www.kaggle.com/models/{url}'
						rows.append({'name': name, 'kaggle_url': url})
				else:
					# Try to treat the top-level dict as a single model
					name = data.get('name') if isinstance(data, dict) else ''
					url = data.get('kaggle_url') if isinstance(data, dict) else ''
					if url:
						rows.append({'name': name, 'kaggle_url': url})
				# Write temporary CSV to /tmp or current working dir
				from tempfile import NamedTemporaryFile
				with NamedTemporaryFile('w', delete=False, newline='', encoding='utf-8', suffix='.csv') as tmpf:
					w = csv.DictWriter(tmpf, fieldnames=['name', 'kaggle_url'])
					w.writeheader()
					for r in rows:
						w.writerow(r)
					tmp_path = tmpf.name
				print(f'Wrote temporary CSV with {len(rows)} rows to {tmp_path}')
				fetch_models_from_csv(tmp_path, output_file=args.output, output_dir=args.output_dir)
				# Attempt to remove temp file
				try:
					os.remove(tmp_path)
				except Exception:
					pass
	elif args.input_json or args.input_csv:
		# handled above
		pass
	else:
		list_models_and_save(page_size=args.page_size, max_pages=args.max_pages, output_file=args.output, filter_keywords=args.filter, output_dir=args.output_dir)
