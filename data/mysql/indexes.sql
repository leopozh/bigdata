USE imdb;

CREATE INDEX idx_ratings_score_votes
ON title_ratings(averageRating, numVotes);

CREATE INDEX idx_episode_parent
ON title_episode(parentTconst);
