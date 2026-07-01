from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Category, Product, Order, OrderItem, Customer

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    # Sử dụng hàm định dạng hiển thị tiền
    list_display = ('name', 'category', 'formatted_price', 'formatted_cost_price', 'stock', 'barcode')
    search_fields = ('name', 'barcode')
    list_filter = ('category',)

    def formatted_price(self, obj):
        return f"{obj.price:,}đ"
    formatted_price.short_description = "Giá bán"

    def formatted_cost_price(self, obj):
        return f"{obj.cost_price:,}đ"
    formatted_cost_price.short_description = "Giá nhập"

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'address', 'birth_year', 'created_at')
    search_fields = ('name', 'phone')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'created_at', 'formatted_total_amount')
    inlines = [OrderItemInline]
    list_filter = ('created_at',)
    
    def formatted_total_amount(self, obj):
        return f"{obj.total_amount:,} VND"
    formatted_total_amount.short_description = "Tổng tiền"
    
    def changelist_view(self, request, extra_context=None):
        chart_and_button_html = mark_safe("""
        <div style="margin-bottom: 25px; background: #fff; padding: 20px; border-radius: 6px; border: 1px solid #dfdfdf; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
           <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px;">
                <h3 style="margin: 0; color: #333; font-weight: 600;">📊 Phân tích Doanh thu & Lợi nhuận thực tế</h3>
                <a href="/bao-cao/export-excel/" style="background: #28a745; color: #fff; padding: 8px 16px; font-weight: bold; text-decoration: none; border-radius: 4px; font-size: 13px;">📥 Xuất Báo Cáo Excel</a>
            </div>
            <div style="width: 100%; height: 300px;">
                <canvas id="revenueChart" style="width: 100%; height: 300px;"></canvas>
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script>
            (function() {
                function initChart() {
                    if (typeof Chart === 'undefined') {
                        setTimeout(initChart, 100);
                        return;
                    }
                    fetch('/bao-cao/revenue-chart-data/')
                        .then(response => response.json())
                        .then(data => {
                            if (!data.labels || data.labels.length === 0) return;
                            const ctx = document.getElementById('revenueChart').getContext('2d');
                            new Chart(ctx, {
                                type: 'bar',
                                data: {
                                    labels: data.labels,
                                    datasets: [
                                        {
                                            label: 'Doanh thu tổng (VND)',
                                            data: data.revenue,
                                            backgroundColor: 'rgba(54, 162, 235, 0.75)',
                                            borderColor: 'rgba(54, 162, 235, 1)',
                                            borderWidth: 1
                                        },
                                        {
                                            label: 'Lợi nhuận thực tế (VND)',
                                            data: data.profit,
                                            backgroundColor: 'rgba(255, 99, 132, 0.75)',
                                            borderColor: 'rgba(255, 99, 132, 1)',
                                            borderWidth: 1
                                        }
                                    ]
                                },
                                options: {
                                    responsive: true,
                                    maintainAspectRatio: false,
                                    scales: { y: { beginAtZero: true } }
                                }
                            });
                        })
                        .catch(err => console.error("Lỗi lấy dữ liệu API:", err));
                }
                
                // FIX: Đổi từ window.readyState thành document.readyState chuẩn cấu trúc DOM
                if (document.readyState === 'complete') {
                    initChart();
                } else {
                    window.addEventListener('load', initChart);
                }
            })();
        </script>
        """)
        
        self.message_user(request, chart_and_button_html)
        return super().changelist_view(request, extra_context=extra_context)
