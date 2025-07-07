from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.
from .models import User, Category, Book, Chapter, TransactionRecord

class UserAdmin(BaseUserAdmin):
    list_display = ("username", "is_staff", "coin")

admin.site.register(User, UserAdmin)

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['display_order', 'name']

admin.site.register(Category, CategoryAdmin)

class ChapterInline(admin.StackedInline):
    model = Chapter
    extra = 1

class BookAdmin(admin.ModelAdmin):
    model = Book
    list_display = ['title', 'published']
    inlines = [ChapterInline]

admin.site.register(Book, BookAdmin)

class TransactionRecordAdmin(admin.ModelAdmin):
    model = TransactionRecord
    list_display = ['kind', 'amount', 'user', 'book', 'datetime']
    list_filter = ['kind']
    search_fields = ['user__username', 'book__title']
    search_help_text = 'ユーザー名と書籍名で検索できます'

admin.site.register(TransactionRecord, TransactionRecordAdmin)
