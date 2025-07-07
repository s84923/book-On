from django.shortcuts import redirect, get_object_or_404
from django.views import generic
from django.contrib.auth import views as auth_views
from django.contrib.auth import mixins as auth_mixins
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy

import csv
import codecs

from .models import User, Book, TransactionRecord
from .forms import UserImportForm, BookSearchForm, CoinChargeForm, CoinUseForm,CoinPurchaseForm

# Create your views here.
class BookSearchMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # フォームの初期値として「送信された検索条件」を設定
        context['search_form'] = BookSearchForm(self.request.GET)
        return context

class HomeView(BookSearchMixin, generic.TemplateView):
    template_name = 'onboro/home.html'

class LoginView(auth_views.LoginView):
    template_name = 'onboro/login.html'

class LogoutView(auth_views.LogoutView):
    pass

def staff_required(user):
    return user.is_staff

class StaffRequiredMixin(auth_mixins.UserPassesTestMixin):
    def test_func(self):
        return staff_required(self.request.user)

class UserIndexView(StaffRequiredMixin, generic.ListView):
    queryset = User.objects.filter(is_staff=False)
    template_name = 'onboro/user_index.html'
    context_object_name = 'users'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['import_form'] = UserImportForm()
        return context

class UserDetailView(StaffRequiredMixin, generic.DetailView):
    queryset = User.objects.filter(is_staff=False)
    template_name = 'onboro/user_detail.html'
    # userという名前はdjango.contrib.authにより設定されるので使えない
    context_object_name = 'object'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['charge_form'] = CoinChargeForm(initial={'user': self.kwargs['pk']})
        return context

# 関数として定義しておいた「スタッフ権限が必要」を使い、一般ユーザーはアクセスできないようにします
@user_passes_test(staff_required)
def user_import(request):
    if request.method == 'POST':
        # 「ファイル内容」以外はPOSTに格納されるので両方を指定します
        form = UserImportForm(request.POST, request.FILES)
        if form.is_valid():
            # validation実行後はcleaned_dataに内容が設定されます
            file = form.cleaned_data['file']
            # fileはバイナリオープンされるのでCSVで読み込むにはdecodeが必要
            reader = csv.DictReader(codecs.iterdecode(file, 'utf-8'))

            try:
                # トランザクションとして実行（一つでもエラーになる場合は全部の追加を取りやめる）
                # with文を使い、その内部に「処理」を書く
                with transaction.atomic():
                    for row in reader:
                        # is_activeはint経由でboolに変換
                        row['is_active'] = bool(int(row['is_active']))
                        # Userはパスワードについて特別処理が必要なため、専用のcreate_userメソッドが用意されている
                        # usernameは一意である必要があるため、同じusernameがあるとIntegrityError（例外）が発生する
                        User.objects.create_user(**row)
                messages.success(request, 'インポートに成功しました。')
            except IntegrityError:
                messages.error(request, 'インポートが行えませんでした。ユーザー名が重複している可能性があります。')

    return redirect('onboro:user_index')

class BookSearchView(BookSearchMixin, generic.ListView):
    template_name = 'onboro/book_search.html'
    context_object_name = 'books'

    def get_queryset(self):
        # BookSearchFormは使わず、直接取得する方がわかりやすい
        category = self.request.GET['category']
        word = self.request.GET['word']

        # 公開しているもののみを対象とする
        books = Book.objects.filter(published=True)
        # カテゴリが設定されていれば条件に加える
        if category:
            books = books.filter(category__pk=category)
        # 検索ワードが指定されていれば条件に加える
        # タイトルと概要は「どちらかに書いてあれば（OR）」でカテゴリとはANDとなる
        if word:
            q1 = Q(title__contains=word)
            q2 = Q(abstract__contains=word)
            books = books.filter(q1 | q2)

        return books

def can_view_chapter(user, book_id):
    if user.is_authenticated:
        if user.is_staff:
            return True
        if user.books.filter(pk=book_id).exists():
            return True

    return False

class BookDetailView(BookSearchMixin, generic.DetailView):
    queryset = Book.objects.filter(published=True)
    template_name = 'onboro/book_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ユーザーが書籍を購入していなければ購入フォームを用意する
        user = self.request.user
        book_pk = self.kwargs['pk']
        if user.is_authenticated:
            if not user.books.filter(pk=book_pk).exists():
                context['use_form'] = CoinUseForm(initial={
                    'user': user.pk,
                    'book': book_pk
                })

        context['can_view_chapter'] = can_view_chapter(user, book_pk)

        return context

class BookChapterView(BookSearchMixin, generic.DetailView):
    template_name = 'onboro/book_chapter.html'

    def get(self, request, *args, **kwargs):
        # 購入していない書籍の章に直アクセスされたら403を返す
        book_id = self.kwargs['book_id']
        if not can_view_chapter(self.request.user, book_id):
            return HttpResponseForbidden()

        return super().get(request, args, kwargs)

    # 指定bookの中の指定chapterなのでget_objectを定義する必要あり
    def get_object(self, queryset=None):
        book_id = self.kwargs['book_id']
        number = self.kwargs['number']
        # 非公開のbookにはアクセスできないようにする
        book = get_object_or_404(Book, pk=book_id, published=True)
        # 存在しない章にアクセスされたとき対策としてこちらもget_or_404を使う
        # get_or_404にはManagerを渡せる
        chapter = get_object_or_404(book.chapter_set, number=number)
        return chapter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get_objectでchapter返すのでchapterが設定される
        chapter = context['chapter']
        # chapterの親もcontextにあった方がいいので設定
        context['book'] = chapter.book
        return context

@user_passes_test(staff_required)
def transaction_charge(request, pk):
    if request.method == 'POST':
        form = CoinChargeForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            # 予想外のことがない限り例外は発生しないのでtry-exceptはしない
            with transaction.atomic():
                user = record.user
                user.coin += record.amount
                user.save()

                record.kind = TransactionRecord.Kind.CHARGE.value
                record.datetime = timezone.now()
                record.save()

    return redirect('onboro:user_detail', pk)

def transaction_use(request, pk):
    # リダイレクト先がbook_detailなのでGETされるのは想定外（Django的にエラーにする）
    if request.method == 'POST':
        form = CoinUseForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            user = record.user
            book = record.book

            if user.coin < book.price:
                messages.warning(request, 'コインが足りません。')
                # コード重複にはなるがインデントが深くなるとわかりにくくなるのでここでreturn
                return redirect('onboro:book_detail', book.pk)

            with transaction.atomic():
                user.coin -= book.price
                user.save()

                record.kind = TransactionRecord.Kind.USE.value
                record.amount = book.price
                record.datetime = timezone.now()
                record.save()

            return redirect('onboro:book_detail', book.pk)

class CoinPurchaseView(auth_mixins.LoginRequiredMixin, generic.FormView):
    template_name = 'onboro/purchase.html'
    form_class = CoinPurchaseForm
    success_url = reverse_lazy('onboro:home')

    def form_valid(self, form):
        amount = form.cleaned_data['amount']
        user = self.request.user

        with transaction.atomic():
            user.coin += amount
            user.save()

            TransactionRecord.objects.create(
                kind=TransactionRecord.Kind.CHARGE,
                amount=amount,
                user=user,
                datetime=timezone.now()
            )

        messages.success(self.request, f'{amount}コインを購入しました。')
        return super().form_valid(form)