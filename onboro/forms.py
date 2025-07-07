from django import forms

from .models import Category, TransactionRecord

class UserImportForm(forms.Form):
    file = forms.FileField(
        widget=forms.FileInput(attrs={'accept': 'text/csv'})
    )

class BookSearchForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), required=False)
    word = forms.CharField(required=False, widget=forms.TextInput(attrs={'type': 'search'}))

class CoinChargeForm(forms.ModelForm):
    class Meta:
        model = TransactionRecord
        fields = ['amount', 'user']
        widgets = {
            'user': forms.HiddenInput
        }

class CoinUseForm(forms.ModelForm):
    class Meta:
        model = TransactionRecord
        fields = {'user', 'book'}
        widgets = {
            'user': forms.HiddenInput,
            'book': forms.HiddenInput
        }


class CoinPurchaseForm(forms.Form):
    amount=forms.IntegerField(label="購入するコインの枚数",min_value=1)
