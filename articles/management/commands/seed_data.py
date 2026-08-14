import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.text import slugify
from articles.models import Category, Tag, Article, Comment
from ads.models import AdSlot
from layout.models import HomepageLayout, SiteSetting, DailyVerse, SocialLink
from newsletter.models import Subscriber
from announcements.models import Announcement

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds realistic, non-technical editorial content for Isezerano digital newspaper'

    def handle(self, *args, **kwargs):
        self.stdout.write('Purging old data...')
        Article.objects.all().delete()
        Category.objects.all().delete()
        Tag.objects.all().delete()
        AdSlot.objects.all().delete()
        HomepageLayout.objects.all().delete()
        SiteSetting.objects.all().delete()
        Subscriber.objects.all().delete()
        DailyVerse.objects.all().delete()
        Announcement.objects.all().delete()
        SocialLink.objects.all().delete()

        self.stdout.write('Seeding database with realistic content...')

        # 1. Create Users
        self.stdout.write('- Creating users...')
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@isezerano.com',
                'first_name': 'Amani',
                'last_name': 'Admin',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('pulse_admin_pass')
            admin_user.save()

        editor_user, created = User.objects.get_or_create(
            username='editor_alex',
            defaults={
                'email': 'alex@isezerano.com',
                'first_name': 'Alex',
                'last_name': 'Editor',
                'role': 'editor',
                'is_staff': True
            }
        )
        if created:
            editor_user.set_password('pulse_editor_pass')
            editor_user.save()

        journalist1, created = User.objects.get_or_create(
            username='writer_elena',
            defaults={
                'email': 'elena@isezerano.com',
                'first_name': 'Elena',
                'last_name': 'Rostova',
                'role': 'journalist',
                'bio': 'Elena reports on design, urban culture, and public spaces.',
                'twitter': 'https://twitter.com/elena_rostova'
            }
        )
        if created:
            journalist1.set_password('pulse_writer_pass')
            journalist1.save()

        journalist2, created = User.objects.get_or_create(
            username='writer_marcus',
            defaults={
                'email': 'marcus@isezerano.com',
                'first_name': 'Marcus',
                'last_name': 'Vance',
                'role': 'journalist',
                'bio': 'Marcus covers business, sustainability practices, and nature conservation.',
                'twitter': 'https://twitter.com/marcus_vance'
            }
        )
        if created:
            journalist2.set_password('pulse_writer_pass')
            journalist2.save()

        reader1, created = User.objects.get_or_create(
            username='reader_jane',
            defaults={
                'email': 'jane@isezerano.com',
                'first_name': 'Jane',
                'last_name': 'Doe',
                'role': 'reader'
            }
        )
        if created:
            reader1.set_password('pulse_reader_pass')
            reader1.save()

        # 2. Create Categories
        self.stdout.write('- Creating categories...')
        business_cat = Category.objects.create(slug='business', name='Business', color_accent='#2a69ac', order=1)
        fashion_cat = Category.objects.create(slug='fashion', name='Fashion', color_accent='#df4d38', order=2)
        culture_cat = Category.objects.create(slug='culture', name='Culture', color_accent='#d8b13a', order=3)
        tech_cat = Category.objects.create(slug='technology', name='Technology', color_accent='#2fb16b', order=4)
        design_cat = Category.objects.create(slug='design', name='Design', color_accent='#df4d38', order=5)
        nature_cat = Category.objects.create(slug='nature', name='Nature', color_accent='#8e5ab1', order=6)
        health_cat = Category.objects.create(slug='health', name='Health', color_accent='#2394ac', order=7)
        sports_cat = Category.objects.create(slug='sports', name='Sports', color_accent='#2F6DF6', order=8)
        faith_cat = Category.objects.create(slug='faith', name='Faith', color_accent='#2F6DF6', order=9)

        # 3. Create Tags
        self.stdout.write('- Creating tags...')
        tags_list = ['Sustainability', 'Local Business', 'Art Galleries', 'Creative Office', 'Conservation', 'Wellbeing', 'Summer Style']
        tags_dict = {}
        for tag_name in tags_list:
            tag = Tag.objects.create(slug=slugify(tag_name), name=tag_name)
            tags_dict[tag_name] = tag

        # 4. Create Articles
        self.stdout.write('- Creating articles...')
        
        # Article 1: Lead Hero (Design/Architecture)
        art1 = Article.objects.create(
            slug='clean-grid-creative-office-spaces',
            title='The Clean Grid: Restructuring Office Spaces for Open Collaboration',
            subtitle='How local architects are designing modern workspaces that prioritize natural light, natural ventilation, and quiet areas for work.',
            body=(
                'In recent years, the structure of the modern workspace has undergone a major shift. '
                'Rather than traditional cubicles or noisy open-plan layouts, designers are turning toward '
                'flexible grid architectures. These designs create modular spaces that can easily be '
                'reconfigured depending on team needs.\n\n'
                '### The Importance of Natural Light\n'
                'One of the key priorities in these new architectural plans is ensuring that natural light '
                'reaches every desk. Studies have shown that access to daylight significantly improves '
                'productivity, mood, and sleep quality for office employees. By placing desks around '
                'the perimeter of the floor and utilizing glass dividers, light flows freely throughout the space.\n\n'
                '### Quiet Spaces and Focus Nodes\n'
                'While collaborative tables are useful for group brainstorming, quiet individual workspaces '
                'are equally critical. Architects are designing small, soundproof phone booths and '
                'dedicated reading rooms where employees can focus on deep work without interruption. '
                'This balance of social and private spaces creates a balanced workplace dynamic.'
            ),
            cover_image='https://images.unsplash.com/photo-1507238691740-187a5b1d37b8?q=80&w=800&auto=format&fit=crop',
            category=design_cat,
            author=journalist1,
            status='published',
            is_breaking=True,
            is_featured=True,
            is_premium=False,
            reading_time=6,
            view_count=1240,
            published_at=timezone.now() - datetime.timedelta(hours=2)
        )
        art1.tags.add(tags_dict['Creative Office'], tags_dict['Sustainability'])

        # Article 2: Business Card
        art2 = Article.objects.create(
            slug='sustainable-commerce-local-logistics',
            title='Sustainable Commerce: Navigating Local Logistics Challenges',
            subtitle='Local supply chain companies are adopting electric fleets and optimized route software to reduce neighborhood carbon outputs.',
            body=(
                'Moving goods across urban centers has always been a logistical challenge. Now, local delivery '
                'companies are rethinking their carbon footprint. By integrating electric delivery trucks '
                'and cargo bikes, businesses are managing to keep shipping times low while decreasing emission values.\n\n'
                '### Route Optimization Tools\n'
                'In addition to cleaner vehicles, companies are utilizing advanced route planning software. '
                'These systems analyze traffic grids in real-time, sending drivers on the most efficient paths '
                'and preventing trucks from idling in neighborhood congestion blocks.'
            ),
            cover_image='https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?q=80&w=800&auto=format&fit=crop',
            category=business_cat,
            author=journalist2,
            status='published',
            is_breaking=False,
            is_featured=False,
            is_premium=False,
            reading_time=4,
            view_count=872,
            published_at=timezone.now() - datetime.timedelta(hours=6)
        )
        art2.tags.add(tags_dict['Local Business'], tags_dict['Sustainability'])

        # Article 3: Fashion Card
        art3 = Article.objects.create(
            slug='minimalist-styles-sustainable-patterns',
            title='Minimalist Styles: The Rise of Sustainable Print Patterns',
            subtitle='How designers are using natural dyes and recycled fibers to craft elegant, durable silhouettes for summer wardrobe setups.',
            body=(
                'Sustainable fashion is no longer a niche market. Designers this summer are focusing heavily on '
                'recyclable materials and ethical production chains. From organic cotton shirts to dresses '
                'dyed with vegetable extracts, the emphasis is on durability and environmental impact.'
            ),
            cover_image='https://images.unsplash.com/photo-1490481651871-ab68de25d43d?q=80&w=800&auto=format&fit=crop',
            category=fashion_cat,
            author=journalist1,
            status='published',
            is_breaking=False,
            is_featured=False,
            is_premium=False,
            reading_time=5,
            view_count=521,
            published_at=timezone.now() - datetime.timedelta(hours=12)
        )
        art3.tags.add(tags_dict['Summer Style'], tags_dict['Sustainability'])

        # Article 4: Nature Card
        art4 = Article.objects.create(
            slug='forest-conservation-upstate-parks',
            title='Forest Conservation Efforts Show Promising Results in Upstate Parks',
            subtitle='Environmental agencies report a healthy recovery of native plant life and stabilized soil banks following a three-year protection program.',
            body=(
                'A joint study by local environmental groups has confirmed that upstate woodlands are undergoing '
                'a major ecological recovery. By controlling traffic paths and replanting native seedlings, '
                'biodiversity index scores have risen by twelve percent.'
            ),
            cover_image='https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?q=80&w=800&auto=format&fit=crop',
            category=nature_cat,
            author=journalist2,
            status='published',
            is_breaking=False,
            is_featured=False,
            is_premium=False,
            reading_time=7,
            view_count=988,
            published_at=timezone.now() - datetime.timedelta(days=1)
        )
        art4.tags.add(tags_dict['Conservation'])

        # Article 5: Culture Card (Premium)
        art5 = Article.objects.create(
            slug='modern-museums-digital-art-preservation',
            title='Modern Museums and the Digital Preservation of Fine Art',
            subtitle='How gallery archives are utilizing high-definition scans and virtual tours to make historical collections accessible to a global audience.',
            body=(
                'Museums around the world are undergoing a quiet revolution. By digitizing their historical galleries '
                'using 3D laser scanners, fine art pieces can be studied by students anywhere in the world. '
                'This preservation effort ensures that even if physical artifacts degrade over centuries, '
                'their digital representations remain perfect for research.'
            ),
            cover_image='https://images.unsplash.com/photo-1513364776144-60967b0f800f?q=80&w=800&auto=format&fit=crop',
            category=culture_cat,
            author=journalist1,
            status='published',
            is_breaking=False,
            is_featured=False,
            is_premium=True,
            reading_time=6,
            view_count=612,
            published_at=timezone.now() - datetime.timedelta(days=2)
        )
        art5.tags.add(tags_dict['Art Galleries'])

        # Article 6: Health Card
        art6 = Article.objects.create(
            slug='balance-recovery-importance-micro-breaks',
            title='Balance and Recovery: The Importance of Micro-Breaks During Workdays',
            subtitle='New research indicates that taking short two-minute walks every hour helps maintain focus and prevents physical strain.',
            body=(
                'Sitting at a desk for eight hours takes a toll on physical health and mental focus. '
                'Health practitioners are urging employees to take brief micro-breaks throughout the day. '
                'Standing up, stretching, or simply looking away from screens for a few minutes helps '
                'relax eyes and keeps energy levels balanced.'
            ),
            cover_image='https://images.unsplash.com/photo-1505751172876-fa1923c5c528?q=80&w=800&auto=format&fit=crop',
            category=health_cat,
            author=journalist2,
            status='published',
            is_breaking=False,
            is_featured=False,
            is_premium=False,
            reading_time=3,
            view_count=1450,
            published_at=timezone.now() - datetime.timedelta(days=3)
        )
        art6.tags.add(tags_dict['Wellbeing'])

        # 5. Create Comments
        self.stdout.write('- Creating comments...')
        Comment.objects.create(
            article=art1,
            user=reader1,
            body="This design is beautiful! I love how clear and quiet the workspaces look. Very inspiring.",
            status='approved'
        )
        Comment.objects.create(
            article=art1,
            user=editor_user,
            body="Excellent writing. It is great to highlight how design directly influences everyday productivity.",
            status='approved'
        )

        # Sports Articles
        art_sports1 = Article.objects.create(
            slug='rayon-sports-defeat-apr-fc',
            title='Rayon Sports yatsinze APR FC mu mukino w’amateka w’igikombe cy’intwari',
            subtitle='Rayon Sports yerekanye umukino ukomeye itsinda APR FC ibitego 2-1 mu mukino wabereye kuri Stade Amahoro imbere y’abafana ibihumbi.',
            body=(
                'Umukino w’ishiraniro wahuje amakipe abiri akomeye mu Rwanda, Rayon Sports na APR FC, '
                'warangiye Rayon Sports yihagazeho yegukana intsinzi. APR FC niyo yafunguye izamu ku munota wa 15 '
                'ku gitego cyatsinzwe na Mugisha Gilbert, ariko Rayon Sports yishyura binyuze kuri Luvumbu '
                'ku munota wa 40, mbere y’uko rutahizamu mushya atsinda igitego cy’intsinzi mu gice cya kabiri.'
            ),
            cover_image='https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=800&auto=format&fit=crop',
            category=sports_cat,
            author=journalist1,
            status='published',
            is_breaking=True,
            is_featured=False,
            is_premium=False,
            reading_time=4,
            view_count=2300,
            published_at=timezone.now() - datetime.timedelta(minutes=30)
        )
        art_sports2 = Article.objects.create(
            slug='kigali-peace-marathon-registration-open',
            title='Kigali Peace Marathon 2026: Iyandikisha ryamaze gutangira ku mugaragaro',
            subtitle='Minisiteri ya Siporo yatangaje ko imyiteguro igeze kure kandi ko abasiganwa bashobora kwiyandikisha binyuze ku rubuga rwa interineti.',
            body=(
                'Kigali International Peace Marathon igiye kuba ku nshuro ya 21, yiteguye kwakira abasiganwa '
                'barenga ibihumbi icumi baturutse mu bihugu bitandukanye by’isi. Abashaka kwitabira '
                'bafite amahirwe yo kwiyandikisha mu cyiciro cya Half Marathon (21km) cyangwa Full Marathon (42km).'
            ),
            cover_image='https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?q=80&w=800&auto=format&fit=crop',
            category=sports_cat,
            author=journalist2,
            status='published',
            is_breaking=False,
            is_featured=False,
            is_premium=False,
            reading_time=3,
            view_count=980,
            published_at=timezone.now() - datetime.timedelta(hours=4)
        )

        # Faith Article
        art_faith1 = Article.objects.create(
            slug='isano-y-ukwemera-no-kubana-neza',
            title='Isano iri hagati y’Ukwemera n’Umubano Mwiza mu Muryango Nyarwanda',
            subtitle='Abayobozi b’amadini atandukanye bagaragaje ko ukwemera nyakuri kugomba kuranga umuntu mu bikorwa bya buri munsi birimo amahoro n’ubwiyunge.',
            body=(
                'Mu nama yahuje abahagarariye amadini n’amatorero mu Rwanda, hagarutswe ku ruhare rw’inyigisho '
                'z’iyobokamana mu kubaka umuryango utekanye kandi utarangwamo amakimbirane. Hagaragajwe ko '
                'amasengesho adaherekejwe n’ibikorwa by’urukundo n’ubworoherane nta mumaro bifitiye sosiyete.'
            ),
            cover_image='https://images.unsplash.com/photo-1438029071396-1e831a7fa6d8?q=80&w=800&auto=format&fit=crop',
            category=faith_cat,
            author=journalist1,
            status='published',
            is_breaking=False,
            is_featured=False,
            is_premium=False,
            reading_time=5,
            view_count=740,
            published_at=timezone.now() - datetime.timedelta(hours=8)
        )

        # 5. Create Comments
        self.stdout.write('- Creating comments...')
        Comment.objects.create(
            article=art1,
            user=reader1,
            body="This design is beautiful! I love how clear and quiet the workspaces look. Very inspiring.",
            status='approved'
        )
        Comment.objects.create(
            article=art1,
            user=editor_user,
            body="Excellent writing. It is great to highlight how design directly influences everyday productivity.",
            status='approved'
        )

        # 6. Create Ad Slots (Wireframe-Accurate Placements)
        self.stdout.write('- Creating ad slots...')
        ad_slots = [
            ('header_banner', 'Qatar Airways Leaderboard', 'https://example.com/airline', 'https://images.unsplash.com/photo-1540962351504-03099e0a754b?q=80&w=800&auto=format&fit=crop'),
            ('hero_sidebar', 'Real Estate Skyscraper', 'https://example.com/property', 'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?q=80&w=800&auto=format&fit=crop'),
            ('daily_verse_sidebar', 'Christian Book Store Ad', 'https://example.com/books', 'https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?q=80&w=800&auto=format&fit=crop'),
            ('news_desk_sidebar', 'Modern Business Advisory', 'https://example.com/advisory', 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?q=80&w=800&auto=format&fit=crop'),
            ('full_width_1', 'MTN Rwanda Data Promotion', 'https://example.com/mtn', 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?q=80&w=800&auto=format&fit=crop'),
            ('full_width_2', 'BK Bank Cashless Campaign', 'https://example.com/bk', 'https://images.unsplash.com/photo-1559526324-4b87b5e36e44?q=80&w=800&auto=format&fit=crop'),
            ('full_width_3', 'RwandAir Flight Promo', 'https://example.com/rwandair', 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?q=80&w=800&auto=format&fit=crop'),
            ('full_width_4', 'Visit Rwanda Tourism campaign', 'https://example.com/visit-rwanda', 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?q=80&w=800&auto=format&fit=crop'),
            ('sports_sidebar', 'Kigali Arena Events Skyscraper', 'https://example.com/arena', 'https://images.unsplash.com/photo-1519766304817-4f37bda74a27?q=80&w=800&auto=format&fit=crop'),
        ]
        for placement, name, target, img in ad_slots:
            AdSlot.objects.create(
                name=name,
                placement=placement,
                target_url=target,
                image=img,
                cta_text='Explore Now',
                start_date=timezone.now(),
                end_date=timezone.now() + datetime.timedelta(days=30),
                priority=1,
                is_active=True
            )

        # Rich Sponsored Content
        AdSlot.objects.create(
            name='Rwanda Revenue Authority: Tax Compliance E-Service Guidance',
            placement='sponsored_content',
            target_url='https://example.com/rra-tax-compliance',
            image='https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?q=80&w=800&auto=format&fit=crop',
            cta_text='Access E-Tax portal',
            sponsored_headline='Taxpayer Information Channel',
            sponsored_video_url='https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            start_date=timezone.now(),
            end_date=timezone.now() + datetime.timedelta(days=30),
            priority=1,
            is_active=True
        )

        # Flyers
        for i in range(1, 4):
            AdSlot.objects.create(
                name=f'Local Business Flyer {i}',
                placement=f'flyer_{i}',
                target_url='https://example.com/flyer-promo',
                image='https://images.unsplash.com/photo-1509281373149-e957c6296406?q=80&w=800&auto=format&fit=crop',
                cta_text='Get Voucher',
                start_date=timezone.now(),
                end_date=timezone.now() + datetime.timedelta(days=30),
                priority=1,
                is_active=True
            )

        # 6.5 Seed Daily Verses
        self.stdout.write('- Creating Daily Verses...')
        DailyVerse.objects.create(
            date=timezone.localdate(),
            verse_reference='Habakuki 2:3',
            verse_text_kinyarwanda='Kuko ibyo kwerekwa bifite igihe byabariwe, kandi bizagera ku ndunduro yabyo ntibizabeshya. Nubwo bitinda uze kubitegereza, kuko kuza ko bizaza ntibizatinda.',
            verse_text_english='For the revelation awaits an appointed time; it speaks of the end and will not prove false. Though it linger, wait for it; it will certainly come and will not delay.'
        )
        DailyVerse.objects.create(
            date=timezone.localdate() - datetime.timedelta(days=1),
            verse_reference='Yohana 3:16',
            verse_text_kinyarwanda='Kuko Imana yakunze abari mu isi cyane, byatumye itanga Umwana wayo w’ikinege kugira ngo umwizera wese atarimbuka, ahubwo ahabwe ubugingo buhoraho.',
            verse_text_english='For God so loved the world that he gave his one and only Son, that whoever believes in him shall not perish but have eternal life.'
        )

        # 6.6 Seed Announcements
        self.stdout.write('- Creating Announcements...')
        Announcement.objects.create(
            title='ITANGAZO RYA GUPIGANIRWA RY’ISOKO RYO GUHAZA AMATA MU BIGO BY’AMASHURI',
            body='QATAR CHARITY RWANDA irashaka gupiganisha isoko ryo guhaza amata mu bigo by’amashuri mu karere ka Bugesera. Abapiganwa bemewe bagomba gutanga amabahasha yabo bitarenze tariki 25 Nyakanga 2026 saa kumi z’umugoroba...',
            announcement_type='amasoko',
            organization_name='QATAR CHARITY RWANDA',
            reference_number='QC/RW/ED/044/2026',
            deadline_date=timezone.localdate() + datetime.timedelta(days=12),
            is_active=True
        )
        Announcement.objects.create(
            title='GUSHAKA ABASEMUZI B’INDIMI EBYIRI (IKINYARWANDA NA ICYONGEREZA)',
            body='BPR Bank Rwanda Plc irashaka gutanga akazi ku basemuzi b’indimi (Ikinyarwanda - Icyongereza). Abifuza gupiganwa bagomba kuba bafite Impamyabumenyi y’icyiciro cya kabiri cya Kaminuza mu zose cyangwa bijyanye...',
            announcement_type='akazi',
            organization_name='BPR Bank Rwanda Plc',
            reference_number='BPR/HR/2026/09',
            deadline_date=timezone.localdate() + datetime.timedelta(days=8),
            is_active=True
        )
        Announcement.objects.create(
            title='URUBANZA RWA MUKAMANA MARIE LOUISE NA GATERA JEAN BAPTISTE',
            body='Urukiko Rwisumbuye rwa Nyarugenge ruramenyesha ko urubanza rwa Mukamana Marie Louise na Gatera Jean Baptiste ku mikoreshereze y’umutungo ruzasomwa kuwa 20 Nyakanga 2026 saa tatu z’igitondo...',
            announcement_type='ibyemezo_by_urukiko',
            organization_name='Urukiko Rwisumbuye rwa Nyarugenge',
            reference_number='RAC/0042/19',
            deadline_date=timezone.localdate() + datetime.timedelta(days=7),
            is_active=True
        )
        Announcement.objects.create(
            title='GUHINDURA AMAKuru y’Amazina yose mu mategeko',
            body='Umusezero Jean Claude uramenyesha ko yifuza guhindura amazina akitwa Umusezero Jean d’Amour mu bitabo by’irangamimerere ku mpamvu z’akazi no guhuza impamyabumenyi ze zose...',
            announcement_type='guhindura_amazina',
            organization_name='Irangamimerere y’Umujyi wa Kigali',
            reference_number='CIV/2026/001',
            deadline_date=timezone.localdate() + datetime.timedelta(days=20),
            is_active=True
        )

        # 7. Homepage Layouts
        self.stdout.write('- Creating homepage layout configuration...')
        HomepageLayout.objects.create(section_type='hero', order=0, article_limit=5)
        HomepageLayout.objects.create(section_type='featured-grid', order=1, article_limit=5)
        HomepageLayout.objects.create(section_type='trending-widget', order=2, article_limit=5)
        HomepageLayout.objects.create(section_type='news-desk', order=3, article_limit=5)
        HomepageLayout.objects.create(section_type='announcements', order=4, article_limit=4)
        HomepageLayout.objects.create(section_type='lifestyle', order=5, article_limit=5)
        HomepageLayout.objects.create(section_type='sports-grid', order=6, article_limit=4)
        HomepageLayout.objects.create(section_type='featured-secondary', order=7, article_limit=5)
        HomepageLayout.objects.create(section_type='category-rail', order=8, category=design_cat, article_limit=5)
        HomepageLayout.objects.create(section_type='flyers', order=9)
        HomepageLayout.objects.create(section_type='you-missed', order=10, article_limit=5)
        HomepageLayout.objects.create(section_type='ad-slot', order=11)

        # 8. Site Settings Singleton
        self.stdout.write('- Creating site settings singleton...')
        SiteSetting.objects.create(
            site_name='Isezerano',
            primary_color='#2F6DF6',
            maintenance_mode=False,
            footer_text='Isezerano Digital Newspaper. Est. 2026.'
        )

        # 9. Subscribers
        self.stdout.write('- Subscribing default emails...')
        Subscriber.objects.create(email='reader.jane@gmail.com')
        Subscriber.objects.create(email='writer.marcus@gmail.com')

        # 10. Social Links
        self.stdout.write('- Seeding default social links...')
        SocialLink.objects.create(platform='facebook', url='https://facebook.com/isezerano', icon_name='facebook', order=0)
        SocialLink.objects.create(platform='twitter', url='https://twitter.com/isezerano', icon_name='twitter', order=1)
        SocialLink.objects.create(platform='instagram', url='https://instagram.com/isezerano', icon_name='instagram', order=2)
        SocialLink.objects.create(platform='youtube', url='https://youtube.com/isezerano', icon_name='youtube', order=3)

        self.stdout.write('Database successfully seeded!')




        #https://unsplash.com/photos/man-in-blue-and-orange-jersey-shirt-running-on-green-grass-field-during-daytime-i8XiabUW3mw
