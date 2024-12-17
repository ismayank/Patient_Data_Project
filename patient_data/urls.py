from django.urls import path
from . import views 

urlpatterns = [
    path('', views.anonymize_patient_data_in_supabase, name='patient_data'),
]
