CREATE DATABASE IF NOT EXISTS imdb CHARACTER SET utf8mb4;
USE imdb;

DROP TABLE IF EXISTS name_basics;
CREATE TABLE name_basics (
  nconst VARCHAR(12) NOT NULL,
  primaryName VARCHAR(255),
  birthYear INT,
  deathYear INT,
  primaryProfession TEXT,
  knownForTitles TEXT,
  PRIMARY KEY (nconst)
);

DROP TABLE IF EXISTS title_akas;
CREATE TABLE title_akas (
  titleId VARCHAR(12) NOT NULL,
  ordering INT NOT NULL,
  title TEXT,
  region VARCHAR(255),
  language VARCHAR(255),
  types TEXT,
  attributes TEXT,
  isOriginalTitle TINYINT(1),
  PRIMARY KEY (titleId, ordering)
);

DROP TABLE IF EXISTS title_basics;
CREATE TABLE title_basics (
  tconst VARCHAR(12) NOT NULL,
  titleType VARCHAR(255),
  primaryTitle TEXT,
  originalTitle TEXT,
  isAdult TINYINT(1),
  startYear INT,
  endYear INT,
  runtimeMinutes INT,
  genres TEXT,
  PRIMARY KEY (tconst)
);

DROP TABLE IF EXISTS title_crew;
CREATE TABLE title_crew (
  tconst VARCHAR(12) NOT NULL,
  directors TEXT,
  writers TEXT,
  PRIMARY KEY (tconst)
);

DROP TABLE IF EXISTS title_episode;
CREATE TABLE title_episode (
  tconst VARCHAR(12) NOT NULL,
  parentTconst VARCHAR(12),
  seasonNumber INT,
  episodeNumber INT,
  PRIMARY KEY (tconst)
);

DROP TABLE IF EXISTS title_principals;
CREATE TABLE title_principals (
  tconst VARCHAR(12) NOT NULL,
  ordering INT NOT NULL,
  nconst VARCHAR(12),
  category VARCHAR(255),
  job TEXT,
  characters TEXT,
  PRIMARY KEY (tconst, ordering)
);

DROP TABLE IF EXISTS title_ratings;
CREATE TABLE title_ratings (
  tconst VARCHAR(12) NOT NULL,
  averageRating DECIMAL(3,1),
  numVotes INT,
  PRIMARY KEY (tconst)
);
