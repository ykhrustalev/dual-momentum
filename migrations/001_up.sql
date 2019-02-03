create table prices
(
  id         bigserial primary key,
  identifier text not null,
  day        date not null,
  open       int  not null,
  close      int  not null
);

create UNIQUE index prices_uniq on prices (identifier, day);