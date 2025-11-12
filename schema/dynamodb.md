 Top-Level Model Fields (18 fields)

  1. id (int)
  2. ref (str)
  3. title (str)
  4. subtitle (str)
  5. author (str)
  6. slug (str) - added by kaggle_api.py script
  7. description (str)
  8. is_private (bool) - may be returned by API
  9. url (str)
  10. publish_time (str) - alternative field name
  11. publishTime (str)
  12. updateTime (str)
  13. provenance_sources (str/list) - alternative field name
  14. provenanceSources (str/list)
  15. voteCount (int)
  16. authorImageUrl (str)
  17. input_name (str) - added by kaggle_api.py script
  18. owner (str) - added by kaggle_api.py script
  19. instances (list) - array of instance objects
  20. tags (list) - array of tag objects
  21. modelVersionLinks (list) - array of link objects

  Model Version Links (2 fields)

  1. type (str)
  2. url (str)

  Tags (8 fields)

  1. ref (str)
  2. name (str)
  3. description (str) - optional
  4. fullPath (str)
  5. competitionCount (int)
  6. datasetCount (int)
  7. scriptCount (int)
  8. totalCount (int)

  Instances (16 fields)

  1. id (int)
  2. slug (str)
  3. framework (str)
  4. fineTunable (bool) - optional
  5. overview (str) - optional
  6. usage (str) - optional
  7. downloadUrl (str) - optional
  8. versionId (int)
  9. versionNumber (int)
  10. url (str)
  11. licenseName (str)
  12. modelInstanceType (str)
  13. totalUncompressedBytes (int)
  14. trainingData (list) - optional
  15. externalBaseModelUrl (str) - optional
  16. baseModelInstanceInformation (dict) - optional, only for variants

  Base Model Instance Information (5 fields)

  1. id (int)
  2. modelSlug (str)
  3. instanceSlug (str)
  4. framework (str)
  5. owner (dict)

  Owner (inside baseModelInstanceInformation, 8 fields)

  1. id (int)
  2. imageUrl (str)
  3. isOrganization (bool)
  4. name (str)
  5. profileUrl (str)
  6. slug (str)
  7. userTier (str)
  8. allowModelGating (bool)