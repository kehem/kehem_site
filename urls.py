from django.urls import path,include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib import admin
from .views import (
    BlogListView,
    BlogDetailView,
    CategoryPostListView,
    TagPostListView,
    BlogSearchView,
    AuthorAdminViewSet,
    BlogPostAdminViewSet,
    CategoryAdminViewSet,
    TagAdminViewSet,
)
from . import invoice_views

blog_post_admin = BlogPostAdminViewSet.as_view({'get': 'list', 'post': 'create'})
blog_post_admin_detail = BlogPostAdminViewSet.as_view({
    'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
})
author_admin = AuthorAdminViewSet.as_view({'get': 'list', 'post': 'create'})
author_admin_detail = AuthorAdminViewSet.as_view({
    'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
})
category_admin = CategoryAdminViewSet.as_view({'get': 'list', 'post': 'create'})
category_admin_detail = CategoryAdminViewSet.as_view({
    'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
})
tag_admin = TagAdminViewSet.as_view({'get': 'list', 'post': 'create'})
tag_admin_detail = TagAdminViewSet.as_view({
    'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'
})
urlpatterns = [
    path('invoice/', invoice_views.invoice_workspace, name="invoice_workspace"),
    path('api/invoices/', invoice_views.invoice_collection_api, name="invoice_collection_api"),
    path('api/invoices/<int:invoice_id>/', invoice_views.invoice_detail_api, name="invoice_detail_api"),
    path('api/invoice-settings/', invoice_views.invoice_settings_api, name="invoice_settings_api"),
    path('',views.index,name="index"),
    path('about',views.about,name="about"),
    path('contact',views.contact,name="contact"),
    path('onuman',views.onuman,name="onuman"),
    path('arafat',views.arafat,name="arafat"),
    path('archdocu',views.archdocu,name="archdocu"),
    path('citrus',views.citrus,name="citrus"),
    path('archimart',views.archimart,name="archimart"),
    path('pricing',views.pricing,name="pricing"),
    path('process',views.process,name="process"),
    path('projects',views.projects,name="projects"),
    path('services',views.services,name="services"),
    path('website-development',views.website_development,name="website_development"),
    path('saas-development',views.saas_development,name="saas_development"),
    path('custom-software-development',views.custom_software_development,name="custom_software_development"),
    path('web-app-development',views.web_app_development,name="web_app_development"),
    path('mvp-development',views.mvp_development,name="mvp_development"),
    path('team',views.team,name="team"),
    path('testimonials',views.testimonials,name="testimonials"),
    path('cookie',views.cookie,name="cookie"),
    path('privacy',views.privacy,name="privacy"),
    path('terms',views.terms,name="terms"),
    path('web-development',views.web,name="web_development"),

    path('robots.txt',views.robots_txt,name="robots_txt"),
    path('llms.txt',views.llms_txt,name="llms_txt"),
    path('sitemap.xml',views.sitemap_xml,name="sitemap_xml"),
    path('api/blog/posts/', blog_post_admin, name="blog_admin_posts"),
    path('api/blog/posts/<int:pk>/', blog_post_admin_detail, name="blog_admin_post_detail"),
    path('api/blog/authors/', author_admin, name="blog_admin_authors"),
    path('api/blog/authors/<int:pk>/', author_admin_detail, name="blog_admin_author_detail"),
    path('api/blog/categories/', category_admin, name="blog_admin_categories"),
    path('api/blog/categories/<int:pk>/', category_admin_detail, name="blog_admin_category_detail"),
    path('api/blog/tags/', tag_admin, name="blog_admin_tags"),
    path('api/blog/tags/<int:pk>/', tag_admin_detail, name="blog_admin_tag_detail"),

    path('home',views.home,name="home"),
    path('webhook',views.facebook_webhook,name="webhook"),
    path('blog',views.blog,name="blog"),
    path('blog_view', views.blog_upload, name="blog_view"),
    path('search/', BlogSearchView.as_view(), name='blog_search'),
    path('category/<slug:slug>/', CategoryPostListView.as_view(), name='category_posts'),
    path('tag/<slug:slug>/', TagPostListView.as_view(), name='tag_posts'),
    path('blog/<slug:slug>/', BlogDetailView.as_view(), name='blog_post_detail'),

    path('blog/<post_id>/<blog_title>',views.blog_post,name="blog_post"),
    path('ffeb12/blog_upload',views.blog_upload,name="blog_upload"),
    path('ffeb12/blog_edit/<int:pk>',views.blog_edit,name="blog_edit"),
    path('video/<str:short_code>/',views.redirect_url,name="redirect_url"),
    path('calculator',views.calc,name="calculator"),
    path('note', views.notes_view, name='notes_view'),
    path('api/note_list', views.notes_list, name='notes_list'),
    path('delete-note', views.delete_note, name='delete_note'),
    path('save-note', views.save_note, name='save_note'),
    path('tasks',views.tasks,name="tasks"),
    path('task/<str:date_str>/', views.get_tasks_for_date, name='get_tasks_for_date'), 
    path('task-add/', views.add_task, name='add_task'),
    path('task-update/', views.update_task, name='add_update'),
    path('task-delete/', views.delete_task, name='add_delete'),

    path('payment', views.payment, name='payment'),
    path('payment1', views.payment1, name='payment1'),
    path('success', views.success, name='success'),
    path('cancel', views.cancel, name='cancel'),

    # note api 
    path('api/send-contact-email/', views.send_contact_email, name='send_contact_email'),
    path('api/kehem_note_list', views.kehem_note_list, name='kehem_note_list'),
    path('api/kehem_note_create', views.kehem_note_create, name='kehem_note_create'),
    path('api/kehem_note_update/<int:note_id>', views.kehem_note_update, name='kehem_note_update'),

    # autoschema
    path('autoschema',views.autoschema,name="autoschema"),
    path('generate/', views.SchemaGeneratorView.as_view(), name='generate_schema'),
    
    # Mastor's Gridder
    path('mastorscdn/mastors_gridder', views.mastor_gridder, name='mastor_gridder'),
    # Mastor's Fluider
    path('mastorscdn/mastors_fluider', views.mastor_fluider, name='mastor_fluider'),

    path('676e11f5b8cf16405f49cba58e6216405f49cba5/admin/', admin.site.urls),
    # path('__debug__/', include('debug_toolbar.urls')),
    # tools 
    path('tools/uuid-generator', views.uuid_generator, name='uuid_generator'),
    path('tools/json-validator', views.json_validator, name='json_validator'),
    path('tools/jwt-decoder', views.jwt_decoder, name='jwt_decoder'),
]
# urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += staticfiles_urlpatterns()

