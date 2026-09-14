create table if not exists applications (
    id serial primary key,
    name varchar(100) not null,
    package_name varchar(200) not null unique,
    category varchar(100) not null,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists app_stats (
    id bigserial primary key,
    application_id integer not null references applications(id),
    min_installs bigint,
    score double precision,
    ratings bigint,
    reviews bigint,
    playstore_updated_at timestamptz,
    version varchar(100),
    ad_supported boolean,
    crawled_at timestamptz not null
);

create index if not exists idx_app_stats_app_time
    on app_stats(application_id, crawled_at desc);

create table if not exists app_reviews (
    id bigserial primary key,
    application_id integer not null references applications(id),
    review_id varchar(200) not null,
    review_at timestamptz,
    user_name text,
    thumbs_up_count integer not null default 0,
    score integer,
    content text,
    crawled_at timestamptz not null,
    unique(application_id, review_id)
);

create index if not exists idx_reviews_app_time
    on app_reviews(application_id, review_at desc);

create table if not exists network_measurements (
    id bigserial primary key,
    application_id integer not null references applications(id),
    scenario varchar(20) not null check (scenario in ('upload', 'download')),
    file_name text not null,
    handshake_rtt_ms double precision,
    retransmission_count integer not null,
    zero_window_count integer not null,
    tcp_reset_count integer not null,
    total_bytes bigint not null,
    payload_bytes bigint not null,
    overhead_ratio double precision not null,
    analyzed_at timestamptz not null
);

create index if not exists idx_network_app_time
    on network_measurements(application_id, analyzed_at desc);

insert into applications(name, package_name, category) values
    ('Telegram', 'org.telegram.messenger', 'messenger'),
    ('Whatsapp', 'com.whatsapp', 'messenger'),
    ('Myirancell', 'com.myirancell', 'operator'),
    ('Mymci', 'ir.mci.ecareapp', 'operator'),
    ('MyRightel', 'ir.rightel.myrightel', 'operator'),
    ('Namava', 'com.shatelland.namava.mobile', 'video'),
    ('Lenz', 'com.likotv', 'video'),
    ('Tamashakhonehtv', 'ir.tamashakhonehtv', 'video'),
    ('Fandogh', 'com.plus9.fandogh', 'word-game'),
    ('Amirza', 'com.BrainLadder.AmirzaGP', 'word-game'),
    ('Samavar', 'com.plus9.samavar', 'word-game'),
    ('Baham', 'ir.android.baham', 'chat-dating'),
    ('Pinno', 'app.pinno', 'chat-dating'),
    ('Instagram', 'com.instagram.android', 'social'),
    ('Facebook', 'com.facebook.katana', 'social'),
    ('Tiktok', 'com.zhiliaoapp.musically', 'social')
on conflict (package_name) do nothing;

update applications
set active = false
where name = 'MyRightel';
