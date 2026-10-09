CREATE TABLE account(
	id VARCHAR(16) PRIMARY KEY 
		CONSTRAINT id_min_length CHECK(LENGTH(id) >= 4 )
		CONSTRAINT id_chars CHECK( id ~ '^[가-힣a-z0-9]+$'  )
		CONSTRAINT id_start_num CHECK( NOT id ~ '^[0-9]' ),
	password VARCHAR(60) NOT NULL,
	join_date TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE record(
	record_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	account_id VARCHAR(16) NOT NULL UNIQUE REFERENCES account(id),
	best_record INTEGER NOT NULL
		CONSTRAINT best_record_min CHECK( best_record >= 100 )
		CONSTRAINT best_record_max CHECK( best_record < 10000 ),
	best_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_record_main ON record (
	best_record ASC, best_at DESC, record_id DESC
);

CREATE TABLE record_his (
	id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
	account_id VARCHAR(16) NOT NULL,
	r1 INTEGER NOT NULL CHECK(r1>=100 AND r1 < 10000),
	r2 INTEGER NOT NULL CHECK(r2>=100 AND r2 < 10000),
	r3 INTEGER NOT NULL CHECK(r3>=100 AND r3 < 10000),
	mean_record INTEGER GENERATED ALWAYS AS (
    ROUND((r1 + r2 + r3) / 3.0) ) STORED,
	elapsed FLOAT NOT NULL CHECK(elapsed > 3.3 AND elapsed < 300),
	ip INET NOT NULL,
	submitted_at TIMESTAMPTZ DEFAULT now() NOT NULL,
	FOREIGN KEY (account_id) REFERENCES account(id) 
);

CREATE INDEX idx_record_his_account_time ON record_his (account_id, submitted_at);