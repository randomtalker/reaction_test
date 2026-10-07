CREATE TABLE account(
	id VARCHAR(16) PRIMARY KEY 
		CONSTRAINT id_min_length CHECK(LENGTH(id) >= 4 )
		CONSTRAINT id_chars CHECK( id ~ '^[a-z0-9]+$'  )
		CONSTRAINT id_start_num CHECK( NOT id ~ '^[0-9]' ),
	password VARCHAR(60) NOT NULL
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