-- 1) میانگین امتیاز کلی فروشگاه و میانگین امتیاز نقدها به تفکیک دسته‌بندی و روز.
select
    a.category,
    date(s.crawled_at) as day,
    avg(s.score) as average_store_score,
    avg(r.score) as average_review_score
from applications a
left join app_stats s on s.application_id = a.id
left join app_reviews r
    on r.application_id = a.id
    and date(r.crawled_at) = date(s.crawled_at)
group by a.category, date(s.crawled_at)
order by day, a.category;


-- 2) تغییرات تعداد نصب و روند آن برای هر اپلیکیشن.
with daily as (
    select
        a.name,
        date(s.crawled_at) as day,
        max(s.min_installs) as installs
    from app_stats s
    join applications a on a.id = s.application_id
    group by a.name, date(s.crawled_at)
)
select
    name,
    day,
    installs,
    installs - lag(installs) over (partition by name order by day) as daily_change
from daily
order by day, name;


-- 3) مقایسه محبوبیت اپلیکیشن‌های دسته گپ و گفت با وضعیت پایداری شبکه آن‌ها.
select
    a.name,
    max(s.min_installs) as installs,
    avg(n.handshake_rtt_ms) as average_rtt_ms,
    avg(n.retransmission_count) as average_retransmissions,
    avg(n.zero_window_count) as average_zero_windows,
    avg(n.tcp_reset_count) as average_resets
from applications a
left join app_stats s on s.application_id = a.id
left join network_measurements n on n.application_id = a.id
where a.category = 'chat-dating'
group by a.name
order by installs desc;


-- 4) سؤال اضافه: کدام اپلیکیشن‌ها تعداد نقد زیادی دارند اما میانگین امتیاز نقدهای آن‌ها پایین است؟
select
    a.name,
    count(*) as review_count,
    avg(r.score) as average_review_score
from app_reviews r
join applications a on a.id = r.application_id
group by a.name
having count(*) >= 10
order by average_review_score asc, review_count desc;


-- 5) سؤال اضافه: ترافیک آپلود یا دانلود، کدام‌یک از نظر مصرف داده بهینه‌تر است؟
select
    a.name,
    n.scenario,
    avg(n.overhead_ratio) as average_overhead_ratio,
    avg(n.payload_bytes) as average_payload_bytes
from network_measurements n
join applications a on a.id = n.application_id
group by a.name, n.scenario
order by a.name, n.scenario;
