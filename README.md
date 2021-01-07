# tesla-race-analyzer
Tool to analyze lap-based races using data from Tesla API scrapers (TeslaMate)

drop database tran;
drop user tran;
create database tran;
create user tran with password 'tran_secret';

db migration
flask db init
flask db migrate
flask db upgrade