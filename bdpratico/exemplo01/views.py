from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.views.generic.edit import UpdateView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from .models import pessoa
from .tables import pessoa_table
from django.contrib.auth import authenticate, login, logout

class pessoa_menu(SingleTableView):
    model = pessoa
    table_class = pessoa_table
    template_name_suffix = '_menu'
    table_pagination = {"per_page": 5}
    template_name = 'exemplo01/pessoa_menu.html'

def index(request):
    print("else")
    usuario = request.POST.get('username')
    senha = request.POST.get('password')
    user = authenticate(username=usuario, password=senha)
    if (user is not None):
        login(request, user)
        request.session['username'] = usuario
        request.session['password'] = senha
        request.session['usernamefull'] = (
            user.get_full_name() if hasattr(user, "get_full_name") else user.get_username()
        )
        print(request.session['username'])
        print(request.session['password'])
        print(request.session['usernamefull'])
        from django.shortcuts import redirect
        return redirect('menu_alias')
    else:
        return render(request, 'index.html')


#def index(request):
#    return HttpResponse("EXEMPLO 01.")

def pagina0(request):
    return render(request, 'pagina0.html')

def pagina1(request):
    return render(request, 'pagina1.html')

def pagina2(request):
    dicionario = {}
    registros = pessoa.objects.all()
    dicionario['pessoas'] = registros
    return render(request, 'pagina2.html', dicionario)

def pagina3(request):
    dicionario = {}
    registros = pessoa.objects.all()
    dicionario['pessoas'] = registros
    return render(request, 'pagina3.html', dicionario)

def pagina4(request):
    nome = request.POST.get('nome')
    email = request.POST.get('email')
    celular = request.POST.get('celular')
    funcao = request.POST.get('funcao')
    nascimento = request.POST.get('nascimento')
    ativo = request.POST.get('ativo')
    print("Nome:", nome)
    print("eMail:", email)
    print("Celular:", celular)
    print("Funcao:", funcao)
    print("Nascimento:", nascimento)
    print("ativo:", ativo)
    return render(request, 'pagina4.html')

def pagina5(request):
    xnome = request.POST.get('nome')
    xemail = request.POST.get('email')
    xcelular = request.POST.get('celular')
    xfuncao = request.POST.get('funcao')
    xnascimento = request.POST.get('nascimento')
    xativo = request.POST.get('ativo')
    print("Nome:", xnome)
    print("eMail:", xemail)
    print("Celular:", xcelular)
    print("Funcao:", xfuncao)
    print("Nascimento:", xnascimento)
    print("ativo:", xativo)
    if (xnome is not None):
        xativo = False
        if (xativo == 'on'):
            xativo = True
            pessoa.objects.create(nome=xnome, email=xemail, celular=xcelular,
            funcao=xfuncao, nascimento=xnascimento, ativo=xativo)
    return render(request, 'pagina5.html')

class pessoa_create(CreateView):
    model = pessoa
    fields = ['nome', 'email', 'celular', 'funcao', 'nascimento', 'ativo']
    success_url = reverse_lazy('pessoa_menu_alias')
    
class pessoa_list(ListView):
    model = pessoa
    queryset = pessoa.objects.filter(ativo=True)

class pessoa_update(UpdateView):
    model = pessoa
    fields = ['nome', 'email', 'celular', 'funcao', 'nascimento', 'ativo']
    success_url = reverse_lazy('pessoa_menu_alias')

class pessoa_delete(DeleteView):
    model = pessoa
    fields = ['nome', 'email', 'celular', 'funcao', 'nascimento', 'ativo']
    template_name_suffix = '_delete'
    success_url = reverse_lazy('pessoa_menu_alias')