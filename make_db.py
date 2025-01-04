import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get environment variables
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')

# Establish a connection to the database
conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST
)
cur = conn.cursor()

create_cult_actions_table = f"""
CREATE TABLE IF NOT EXISTS public.cult_actions
(
    uid uuid NOT NULL,
    date timestamp without time zone NOT NULL,
    wallet "char"[] NOT NULL,
    xrp_deposit double precision NOT NULL,
    cult_deposit double precision NOT NULL,
    single_cult_deposit boolean NOT NULL,
    xrp_withdraw double precision NOT NULL,
    cult_withdraw double precision NOT NULL,
    single_cult_withdraw boolean NOT NULL,
    CONSTRAINT cult_actions_pkey PRIMARY KEY (uid)
)
"""
cur.execute(create_cult_actions_table)

create_obey_actions_table = f"""
CREATE TABLE IF NOT EXISTS public.obey_actions
(
    uid uuid NOT NULL,
    date timestamp without time zone NOT NULL,
    wallet "char"[] NOT NULL,
    xrp_deposit double precision NOT NULL,
    obey_deposit double precision NOT NULL,
    single_obey_deposit boolean NOT NULL,
    xrp_withdraw double precision NOT NULL,
    obey_withdraw double precision NOT NULL,
    single_obey_withdraw boolean NOT NULL,
    CONSTRAINT obey_actions_pkey PRIMARY KEY (uid)
)
"""
cur.execute(create_obey_actions_table)

create_cult_daily_record = f"""
CREATE TABLE IF NOT EXISTS public.cult_daily_record
(
    uid uuid NOT NULL,
    date timestamp without time zone NOT NULL,
    wallet "char"[] NOT NULL,
    balance double precision NOT NULL,
    CONSTRAINT cult_daily_record_pkey PRIMARY KEY (uid)
);
"""
cur.execute(create_cult_daily_record)

create_obey_daily_record = f"""
CREATE TABLE IF NOT EXISTS public.obey_daily_record
(
    uid uuid NOT NULL,
    date timestamp without time zone NOT NULL,
    wallet "char"[] NOT NULL,
    balance double precision NOT NULL,
    CONSTRAINT obey_daily_record_pkey PRIMARY KEY (uid)
);
"""
cur.execute(create_obey_daily_record)

create_cult_probation = f"""
CREATE TABLE IF NOT EXISTS public.cult_probation
(
    uid uuid NOT NULL,
    wallet "char"[] NOT NULL,
    probation boolean NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
    CONSTRAINT cult_probation_pkey PRIMARY KEY (uid)
);
"""
cur.execute(create_cult_probation)

create_obey_probation = f"""
CREATE TABLE IF NOT EXISTS public.obey_probation
(
    uid uuid NOT NULL,
    wallet "char"[] NOT NULL,
    probation boolean NOT NULL,
    start_date timestamp without time zone NOT NULL,
    end_date timestamp without time zone NOT NULL,
    CONSTRAINT obey_probation_pkey PRIMARY KEY (uid)
);
"""
cur.execute(create_obey_probation)

create_cult_sent = f"""
CREATE TABLE IF NOT EXISTS public.cult_sent
(
    uid uuid NOT NULL,
    date timestamp without time zone NOT NULL,
    wallet "char"[] NOT NULL,
    amount double precision NOT NULL,
    CONSTRAINT cult_sent_pkey PRIMARY KEY (uid)
);
"""
cur.execute(create_cult_sent)

create_obey_sent = f"""
CREATE TABLE IF NOT EXISTS public.obey_sent
(
    uid uuid NOT NULL,
    date timestamp without time zone NOT NULL,
    wallet "char"[] NOT NULL,
    amount double precision NOT NULL,
    CONSTRAINT obey_sent_pkey PRIMARY KEY (uid)
);
"""
cur.execute(create_obey_sent)

conn.commit()