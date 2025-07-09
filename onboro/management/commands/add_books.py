import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction

from onboro.models import Category, Book, Chapter

class Command(BaseCommand):
    help = '指定された数のサンプル書籍と章をデータベースに自動で追加します。'

    def handle(self, *args, **options):
        """
        コマンド実行時のメイン処理
        """
        # Fakerを日本語で利用する設定
        faker = Faker('ja_JP')

        self.stdout.write(self.style.SUCCESS('--- 書籍の自動追加処理を開始します ---'))

        # カテゴリが存在しない場合はエラーメッセージを表示
        if not Category.objects.exists():
            self.stdout.write(self.style.ERROR('エラー: 書籍を追加する前に、少なくとも1つのカテゴリを登録してください。'))
            return

        try:
            # データベースへの書き込みをトランザクション内で実行
            with transaction.atomic():
                # 登録済みのカテゴリをランダムに取得するためにリスト化
                categories = list(Category.objects.all())

                for i in range(10):  # 10冊の書籍を作成
                    book_title = f"{faker.word()}についての考察"
                    book = Book.objects.create(
                        category=random.choice(categories), # カテゴリをランダムに選択
                        title=book_title,
                        abstract=faker.text(max_nb_chars=200),
                        price=random.randint(500, 3000),
                        published=True # デフォルトで公開状態にする
                    )

                    for j in range(1, 6):  # 各書籍に5つの章を作成
                        Chapter.objects.create(
                            book=book,
                            number=j,
                            title=f"{faker.catch_phrase()}",
                            body=faker.text(max_nb_chars=1000)
                        )
                    
                    self.stdout.write(f'書籍「{book.title}」とその章を追加しました。({i + 1}/10)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            self.stdout.write(self.style.ERROR('処理をロールバックしました。'))
            return

        self.stdout.write(self.style.SUCCESS('--- 全ての書籍の追加が完了しました ---'))
