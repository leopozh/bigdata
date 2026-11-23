USE imdb;

LOAD DATA LOCAL INFILE 'data/clean/name_basics.csv'
INTO TABLE name_basics
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@nconst, @primaryName, @birthYear, @deathYear, @primaryProfession, @knownForTitles)
SET
  nconst = NULLIF(@nconst, ''),
  primaryName = NULLIF(@primaryName, ''),
  birthYear = NULLIF(@birthYear, ''),
  deathYear = NULLIF(@deathYear, ''),
  primaryProfession = NULLIF(@primaryProfession, ''),
  knownForTitles = NULLIF(@knownForTitles, '');

LOAD DATA LOCAL INFILE 'data/clean/title_akas.csv'
INTO TABLE title_akas
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@titleId, @ordering, @title, @region, @language, @types, @attributes, @isOriginalTitle)
SET
  titleId = NULLIF(@titleId, ''),
  ordering = NULLIF(@ordering, ''),
  title = NULLIF(@title, ''),
  region = NULLIF(@region, ''),
  language = NULLIF(@language, ''),
  types = NULLIF(@types, ''),
  attributes = NULLIF(@attributes, ''),
  isOriginalTitle = NULLIF(@isOriginalTitle, '');

LOAD DATA LOCAL INFILE 'data/clean/title_basics.csv'
INTO TABLE title_basics
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@tconst, @titleType, @primaryTitle, @originalTitle, @isAdult, @startYear, @endYear, @runtimeMinutes, @genres)
SET
  tconst = NULLIF(@tconst, ''),
  titleType = NULLIF(@titleType, ''),
  primaryTitle = NULLIF(@primaryTitle, ''),
  originalTitle = NULLIF(@originalTitle, ''),
  isAdult = NULLIF(@isAdult, ''),
  startYear = NULLIF(@startYear, ''),
  endYear = NULLIF(@endYear, ''),
  runtimeMinutes = NULLIF(@runtimeMinutes, ''),
  genres = NULLIF(@genres, '');

LOAD DATA LOCAL INFILE 'data/clean/title_crew.csv'
INTO TABLE title_crew
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@tconst, @directors, @writers)
SET
  tconst = NULLIF(@tconst, ''),
  directors = NULLIF(@directors, ''),
  writers = NULLIF(@writers, '');

LOAD DATA LOCAL INFILE 'data/clean/title_episode.csv'
INTO TABLE title_episode
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@tconst, @parentTconst, @seasonNumber, @episodeNumber)
SET
  tconst = NULLIF(@tconst, ''),
  parentTconst = NULLIF(@parentTconst, ''),
  seasonNumber = NULLIF(@seasonNumber, ''),
  episodeNumber = NULLIF(@episodeNumber, '');

LOAD DATA LOCAL INFILE 'data/clean/title_principals.csv'
INTO TABLE title_principals
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@tconst, @ordering, @nconst, @category, @job, @characters)
SET
  tconst = NULLIF(@tconst, ''),
  ordering = NULLIF(@ordering, ''),
  nconst = NULLIF(@nconst, ''),
  category = NULLIF(@category, ''),
  job = NULLIF(@job, ''),
  characters = NULLIF(@characters, '');

LOAD DATA LOCAL INFILE 'data/clean/title_ratings.csv'
INTO TABLE title_ratings
CHARACTER SET utf8mb4
FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY ''
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(@tconst, @averageRating, @numVotes)
SET
  tconst = NULLIF(@tconst, ''),
  averageRating = NULLIF(@averageRating, ''),
  numVotes = NULLIF(@numVotes, '');
