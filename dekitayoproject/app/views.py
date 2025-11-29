from django.shortcuts import render
from . import forms

def signup(request):
    User_form = forms.UsersModelForm()
    Family_members_form = forms.Family_membersModelForm()

    if request.method == 'POST':
        User_form = forms.UsersModelForm(request.POST)
        Family_members_form = forms.Family_membersModelForm(request.POST)
        if User_form.is_valid() and Family_members_form.is_valid():
            User_form.save()
            Family_members_form.save()
            return redirect('home')

    return render(
        request, 
        'app/signup.html', 
        context={
            'signup': User_form,
            'role': Family_members_form,
        }
    )