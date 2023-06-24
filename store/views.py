from django.shortcuts import render, redirect
from .models import Product, ReviewRating
from category.models import Category
from django.core import paginator
from django.db.models import Q
from django.core.paginator import Paginator
from .forms import ReviewForm
from django.contrib import messages


# Create your views here.
def store(request, category_slug=None):
    if category_slug != None:
        categories = Category.objects.get(slug=category_slug)
        products = Product.objects.filter(category=categories)
        paginator = Paginator(products, 3)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)
        products_count = products.count()
    else:
        products = Product.objects.filter(is_available=True)
        paginator = Paginator(products, 3)
        page = request.GET.get("page")
        paged_products = paginator.get_page(page)
        products_count = products.count()
    context = {
        "products": paged_products,
        "product_count": products_count,
    }
    return render(request, "store/store.html", context)


def product_detail(request, category_slug, product_slug):
    single_product = Product.objects.get(
        category__slug=category_slug, slug=product_slug
    )
    context = {
        "single_product": single_product,
    }
    return render(request, "store/product_details.html", context)


def search(request):
    if "keyword" in request.GET:
        keyword = request.GET.get("keyword")
        if keyword:
            products = Product.objects.order_by("-upload_date").filter(
                Q(description__icontains=keyword) | Q(product_name__icontains=keyword)
            )
            product_count = products.count()
            context = {
                "products": products,
                "product_count": product_count,
            }
    else:
        return redirect("store")
    return render(request, "store/store.html", context)


def submit_review(request, product_id):
    url = request.META.get("HTTP_REFERER")
    if request.method == "POST":
        try:
            reviews = ReviewRating.objects.get(
                user__id=request.user.id, product__id=product_id
            )
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, "Thank you! Your review has been updated")
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data["subject"]
                data.rating = form.cleaned_data["rating"]
                data.review = form.cleaned_data["review"]
                data.ip = request.META.get("REMOTE_ADDR")
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, "Thank you! Your review has been submitted")
                return redirect(url)
    return render(request, "product_detail.html")
