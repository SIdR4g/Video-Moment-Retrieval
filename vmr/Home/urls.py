from django.urls import path,include
from .import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
	path('',views.home,name='home'),
	path('upload/',views.upload_video,name='upload_video'),
	path('analyze/',views.analyze,name='analyze'),
    path('signup/',views.signup,name="signup"),
    path('login/',views.user_login,name="login"),
    path('logout/',views.user_logout,name="logout"),
    path('contact/',views.contact,name="contact"),
    path('archive/',views.get_archive,name="archive"),
    path('sports-analysis/',views.sports_analysis,name="sports_analysis"),
    path('video-editing-assistant/',views.video_editing_assistant,name="video_editing_assistant"),
    path('security-footage-analysis/',views.security_footage_analysis,name="security_footage_analysis"),
    path('media-monitoring/',views.media_monitoring,name="media_monitoring"),
]+static(settings.STATIC_URL,document_root=settings.STATIC_ROOT)