from django.urls import path
from . import views

urlpatterns = [
    path('', views.pos_view, name='pos_home'),
    path('invoice/<int:order_id>/', views.invoice_view, name='print_invoice'),
    
    # ĐỔI THÀNH NHƯ THẾ NÀY (Bỏ chữ admin/ ở đầu đi):
    path('bao-cao/revenue-chart-data/', views.revenue_chart_data, name='revenue_chart_data'),
    path('bao-cao/export-excel/', views.export_revenue_excel, name='export_revenue_excel'), # Đảm bảo tên hàm đúng với views.py
    path('bao-cao/thue/', views.tax_report_view, name='tax_report'),
]
