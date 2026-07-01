import openpyxl
import json
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.admin.views.decorators import staff_member_required
from django.template.loader import render_to_string
from django.db.models import Sum, F, Count
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from .models import Product, Order, OrderItem, Customer

# CẤU HÌNH TÀI KHOẢN NGÂN HÀNG CỦA CỬA HÀNG
BANK_ID = "tcb"          # Mã ngân hàng (Ví dụ: vcb = Vietcombank, tcb = Techcombank, bidv = BIDV)
BANK_ACCOUNT = "1234567890" # Số tài khoản ngân hàng của bạn
BANK_ACCOUNT_NAME = "NGUYEN VAN A" # Tên chủ tài khoản (Viết hoa không dấu)

@staff_member_required
def pos_view(request):
    products = Product.objects.all()
    cart = request.session.get('cart', {})

    if request.method == "POST":
        action = request.POST.get('action')
        success = False
        message = ""

        if action == 'scan_barcode':
            barcode = request.POST.get('barcode', '').strip()
            if barcode:
                try:
                    product = Product.objects.get(barcode=barcode)
                    product_id_str = str(product.id)
                    current_qty = cart.get(product_id_str, 0)
                    
                    if product.stock >= current_qty + 1:
                        cart[product_id_str] = current_qty + 1
                        request.session['cart'] = cart
                        request.session.modified = True
                        success = True
                        message = f"Đã thêm {product.name}"
                    else:
                        message = f"Sản phẩm {product.name} đã hết hàng hoặc vượt quá tồn kho!"
                except Product.DoesNotExist:
                    message = "Không tìm thấy sản phẩm với mã vạch này!"

        elif action == 'add_to_cart':
            product_id = request.POST.get('product_id')
            quantity = int(request.POST.get('quantity', 1))
            try:
                product = Product.objects.get(id=product_id)
                product_id_str = str(product_id)
                current_qty = cart.get(product_id_str, 0)
                
                if product.stock >= current_qty + quantity:
                    cart[product_id_str] = current_qty + quantity
                    request.session['cart'] = cart
                    request.session.modified = True
                    success = True
                    message = f"Đã thêm vào giỏ hàng."
                else:
                    message = "Số lượng yêu cầu vượt quá lượng tồn kho!"
            except Product.DoesNotExist:
                message = "Sản phẩm không tồn tại!"

        elif action == 'remove_from_cart':
            product_id_str = str(request.POST.get('product_id'))
            if product_id_str in cart:
                del cart[product_id_str]
                request.session['cart'] = cart
                request.session.modified = True
                success = True
                message = "Đã xóa sản phẩm khỏi giỏ."

        elif action == 'checkout':
            if cart:
                phone = request.POST.get('customer_phone', '').strip()
                name = request.POST.get('customer_name', '').strip()
                address = request.POST.get('customer_address', '').strip()
                birth_year_raw = request.POST.get('customer_birth_year', '').strip()
                
                birth_year = int(birth_year_raw) if birth_year_raw.isdigit() else None
                customer = None
                
                if phone:
                    try:
                        customer = Customer.objects.get(phone=phone)
                        if name: customer.name = name
                        if address: customer.address = address
                        if birth_year: customer.birth_year = birth_year
                        customer.save()
                    except Customer.DoesNotExist:
                        customer = Customer.objects.create(
                            name=name if name else f"Khách mua lẻ {phone}",
                            phone=phone,
                            address=address,
                            birth_year=birth_year
                        )

                order = Order.objects.create(customer=customer, total_amount=0)
                total_amount = 0
                
                for product_id_raw, quantity in cart.items():
                    try:
                        product = Product.objects.get(id=int(product_id_raw))
                        if product.stock >= quantity:
                            item_total = product.price * quantity
                            total_amount += item_total
                            
                            OrderItem.objects.create(
                                order=order,
                                product=product,
                                quantity=quantity,
                                price=product.price,
                                cost_price=product.cost_price
                            )
                            product.stock -= quantity
                            product.save()
                    except Product.DoesNotExist:
                        pass
                
                order.total_amount = total_amount
                order.save()
                
                request.session['cart'] = {}
                request.session.modified = True
                return redirect('print_invoice', order_id=order.id)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            cart_items = []
            cart_total = 0
            for p_id, qty in cart.items():
                try:
                    prod = Product.objects.get(id=int(p_id))
                    t_price = prod.price * qty
                    cart_total += t_price
                    cart_items.append({'product': prod, 'quantity': qty, 'total_price': t_price})
                except Product.DoesNotExist:
                    continue
            
            qr_url = ""
            if cart_total > 0:
                memo = "THANH TOAN POS"
                qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{BANK_ACCOUNT}-qr_only.png?amount={cart_total}&addInfo={memo}&accountName={BANK_ACCOUNT_NAME}"

            cart_html = render_to_string('store/partials/cart_section.html', {
                'cart_items': cart_items,
                'cart_total': cart_total
            }, request=request)
            
            return JsonResponse({
                'success': success, 
                'message': message, 
                'cart_html': cart_html,
                'qr_url': qr_url
            })

    cart_items = []
    cart_total = 0
    for product_id_raw, quantity in cart.items():
        try:
            product = Product.objects.get(id=int(product_id_raw))
            total_price = product.price * quantity
            cart_total += total_price
            cart_items.append({'product': product, 'quantity': quantity, 'total_price': total_price})
        except Product.DoesNotExist:
            continue

    return render(request, 'store/pos.html', {'products': products, 'cart_items': cart_items, 'cart_total': cart_total})


def invoice_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'store/invoice.html', {'order': order})


@staff_member_required
def revenue_chart_data(request):
    orders = Order.objects.all().order_by('-id')[:10][::-1]
    labels = []
    revenue_data = []
    profit_data = []
    
    for order in orders:
        labels.append(f"Đơn #{order.id}")
        revenue_data.append(order.total_amount)
        
        daily_profit = order.items.aggregate(
            total_profit=Sum(F('quantity') * (F('price') - F('cost_price')))
        )['total_profit'] or 0
        profit_data.append(daily_profit)
        
    return JsonResponse({
        'labels': labels,
        'revenue': revenue_data,
        'profit': profit_data,
    })


@staff_member_required
def export_revenue_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Báo cáo doanh thu"
    
    headers = ["Mã Đơn", "Thời gian", "Doanh thu (VND)", "Tiền vốn (VND)", "Lợi nhuận thực tế (VND)"]
    ws.append(headers)
    
    orders = Order.objects.all().order_by('-id')
    for order in orders:
        total_revenue = 0
        total_cost = 0
        
        for item in order.items.all():
            total_revenue += item.price * item.quantity
            cost_price = item.cost_price if item.cost_price is not None else 0
            total_cost += cost_price * item.quantity

        profit = total_revenue - total_cost
        
        ws.append([
            f"#{order.id}",
            order.created_at.strftime("%d/%m/%Y %H:%M"),
            order.total_amount,
            total_cost,
            profit
        ])
        
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=bao_cao_doanh_thu.xlsx"
    wb.save(response)
    return response


# --- ĐÃ FIX LỖI CÚ PHÁP VÀ ĐỊNH DẠNG SẠCH SẼ HÀM BÁO CÁO THUẾ ---
@staff_member_required
def tax_report_view(request):
    # Lấy giá trị year từ URL dưới dạng chuỗi
    year_raw = request.GET.get('year', '')
    
    # Dọn dẹp bỏ tất cả dấu chấm (.) hoặc dấu phẩy (,) sinh ra do định dạng phân tách hàng nghìn từ Front-end
    if year_raw:
        year_raw = str(year_raw).replace('.', '').replace(',', '')
    
    # Kiểm tra nếu là chuỗi số hợp lệ thì ép kiểu sang int, nếu không mặc định lấy năm hiện tại
    current_year = int(year_raw) if year_raw.isdigit() else timezone.now().year
    
    # Gom nhóm dữ liệu đơn hàng theo từng tháng trong năm được chọn
    monthly_data = Order.objects.filter(created_at__year=current_year) \
        .annotate(month=TruncMonth('created_at')) \
        .values('month') \
        .annotate(
            total_revenue=Sum('total_amount'),
            order_count=Count('id')
        ).order_by('month')

    report_list = []
    
    # Khởi tạo dữ liệu trống cho cả 12 tháng
    for m in range(1, 13):
        report_list.append({
            'month_label': f"Tháng {m}/{current_year}",
            'order_count': 0,
            'revenue': 0,
            'vat_tax': 0,    # Thuế GTGT (1%)
            'pit_tax': 0,    # Thuế TNCN (0.5%)
            'total_tax': 0   # Tổng thuế phải nộp
        })

    # Đổ dữ liệu thực tế từ Database vào danh sách 12 tháng
    for data in monthly_data:
        month_idx = data['month'].month - 1
        revenue = data['total_revenue'] or 0
        order_count = data['order_count'] or 0
        
        report_list[month_idx]['order_count'] = order_count
        report_list[month_idx]['revenue'] = revenue

    # Tính tổng doanh thu thực tế của cả năm trước để xét duyệt có hiệu lực tính thuế hay không
    yearly_revenue = sum(item['revenue'] for item in report_list)
    yearly_orders = sum(item['order_count'] for item in report_list)
    
    # --- XÉT NGƯỠNG MIỄN THUẾ LUẬT ĐỊNH: Hộ kinh doanh doanh thu <= 100 triệu/năm được miễn thuế ---
    if yearly_revenue > 100000000:
        # Nếu doanh thu năm > 100 triệu, tiến hành tính thuế cho từng tháng
        for item in report_list:
            revenue = item['revenue']
            vat = int(revenue * 0.01)       # 1% VAT cho đại lý/tạp hóa bán lẻ
            pit = int(revenue * 0.005)      # 0.5% TNCN
            
            item['vat_tax'] = vat
            item['pit_tax'] = pit
            item['total_tax'] = vat + pit
    else:
        # Nếu tổng cả năm <= 100 triệu, toàn bộ các tháng được miễn thuế (về 0đ)
        for item in report_list:
            item['vat_tax'] = 0
            item['pit_tax'] = 0
            item['total_tax'] = 0

    # Tính tổng kết số tiền thuế thực tế phải nộp sau khi áp dụng luật
    yearly_tax = sum(item['total_tax'] for item in report_list)

    # Tạo danh sách các năm để bộ lọc lựa chọn trên giao diện
    available_years = range(2024, timezone.now().year + 1)

    context = {
        'report_list': report_list,
        'selected_year': current_year,
        'available_years': available_years,
        'yearly_revenue': yearly_revenue,
        'yearly_tax': yearly_tax,
        'yearly_orders': yearly_orders,
    }
    return render(request, 'store/tax_report.html', context)