import random
from faker import Faker
from django.core.management.base import BaseCommand
from django.db import transaction

from onboro.models import Category, Book, Chapter

class Command(BaseCommand):
    help = 'プログラミング関連のサンプル書籍と章をデータベースに自動で追加します。'

    def handle(self, *args, **options):
        """
        コマンド実行時のメイン処理
        """
        # Fakerを日本語で利用する設定
        faker = Faker('ja_JP')
        
        # プログラミング関連のキーワード
        programming_keywords = [
            'Python', 'JavaScript', 'Java', 'Go', 'Rust', 'TypeScript', 'Ruby', 'Swift', 'Kotlin', 'PHP',
            'Web開発', '機械学習', 'データサイエンス', 'アルゴリズム', 'データベース', 'クラウド', 'セキュリティ',
            'フロントエンド', 'バックエンド', 'Django', 'React', 'Vue.js', 'Next.js', 'Docker', 'Git'
        ]

        self.stdout.write(self.style.SUCCESS('--- プログラミング書籍の自動追加処理を開始します ---'))

        try:
            # 「プログラミング」カテゴリを取得、存在しない場合は作成
            programming_category, created = Category.objects.get_or_create(
                name='プログラミング',
                # 新規作成の場合のデフォルト値を設定
                defaults={'display_order': 99} 
            )
            if created:
                self.stdout.write(self.style.WARNING('「プログラミング」カテゴリが存在しなかったため、自動で作成しました。'))

            # データベースへの書き込みをトランザクション内で実行
            with transaction.atomic():
                for i in range(10):  # 10冊の書籍を作成
                    keyword = random.choice(programming_keywords)
                    book_title = f"{keyword}入門"
                    
                    book, created = Book.objects.get_or_create(
                        title=book_title,
                        category=programming_category,
                        defaults={
                            'abstract': f'{keyword}の基礎から応用までを網羅的に解説する一冊です。{faker.text(max_nb_chars=100)}',
                            'price': random.randint(1500, 4500),
                            'published': True
                        }
                    )
                    
                    # 既に同じタイトルの本が存在する場合はスキップ
                    if not created:
                        self.stdout.write(f'書籍「{book.title}」は既に存在するため、スキップしました。')
                        continue

                    for j in range(1, 6):  # 各書籍に5つの章を作成
                        Chapter.objects.create(
                            book=book,
                            number=j,
                            title=f"第{j}章: {keyword}の基本",
                            body=faker.text(max_nb_chars=1000)
                        )
                    
                    self.stdout.write(f'書籍「{book.title}」とその章を追加しました。({i + 1}/10)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'エラーが発生しました: {e}'))
            self.stdout.write(self.style.ERROR('処理をロールバックしました。'))
            return

        self.stdout.write(self.style.SUCCESS('--- 全ての書籍の追加が完了しました ---'))
