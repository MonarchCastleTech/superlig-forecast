create table players(player_id bigint, name varchar, current_club_id bigint);
insert into players values (10, 'Example Player', 1);
create table player_valuations(
  player_id bigint, date date, market_value_in_eur bigint,
  current_club_id bigint, player_club_domestic_competition_id varchar
);
insert into player_valuations values (10, '2025-07-01', 12000000, 1, 'TR1');
create table transfers(player_id bigint, transfer_date date, from_club_id bigint, to_club_id bigint);
create table appearances(appearance_id varchar, player_id bigint, game_id bigint, minutes_played int);
create table games(game_id bigint, competition_id varchar, season int);
insert into games values (100, 'TR1', 2025);
create table game_lineups(game_id bigint, player_id bigint, type varchar, position varchar);
