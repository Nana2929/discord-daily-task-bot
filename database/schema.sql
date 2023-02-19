-- CREATE DATABASE leetbot;

CREATE TABLE IF NOT EXISTS blacklist (
  id int PRIMARY KEY NOT NULL,
  user_id varchar(20) NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- GRANT ALL PRIVILEGES ON DATABASE leetcode TO leetcode;

CREATE TABLE IF NOT EXISTS warns (
  id int PRIMARY KEY NOT NULL,
  user_id varchar(20) NOT NULL,
  server_id varchar(20) NOT NULL,
  moderator_id varchar(20) NOT NULL,
  reason varchar(255) NOT NULL,
  created_at timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS leetcode_daily_challenge (
    id SERIAL PRIMARY KEY,
    member_name varchar(255) NOT NULL,
    report_time timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ldc_subscription (
    member_name varchar(255) PRIMARY KEY NOT NULL,
    remind_time int NOT NULL DEFAULT 20,
    condemn_time int NOT NULL DEFAULT 23
);

