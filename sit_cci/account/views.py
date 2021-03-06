
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.core.signing import BadSignature, SignatureExpired, loads, dumps
from django.http import HttpResponse, Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views import generic

from .forms import LoginForm, UserCreateForm
from member.models import Profile

User = get_user_model()

class Login(LoginView):
    form_class = LoginForm
    template_name = 'account/login.html'

class Logout(LogoutView):
    template_name = 'account/logout.html'

# メール送信のテスト
def send_email(request):
    subject = "題名"
    message = "本文\\nです"
    user = request.user  # ログインユーザーを取得する
    from_email = 'sitdigicrecircle@gmail.com'  # 送信者
    user.email_user(subject, message, from_email)  # メールの送信

    return HttpResponse(str(user.email) + "にメール送信を行いました")

# ユーザー仮登録
class UserCreate(generic.CreateView):
    
    template_name = 'account/user_create.html'
    form_class = UserCreateForm

    # 仮登録と本登録用メールの発行
    def form_valid(self, form):
        # 仮登録と本登録の切り替えは、is_active属性を使う
        # 退会処理も、is_activeをFalseにする
        user = form.save(commit=False)
        user.is_active = False
        # 便宜的に、メールアドレスの最初の7文字を学生番号とみなし、ユーザーネームとする。
        user.username = user.email[:7]
        user.save()
        

        # アクティベーションURLの送付
        current_site = get_current_site(self.request)
        domain = current_site.domain
        context = {
            'protocol': self.request.scheme,
            'domain': domain,
            'token': dumps(user.pk), # tokenを生成
            'user': user,
        }

        subject = render_to_string('account/mail_template/create/subject.txt', context)
        message = render_to_string('account/mail_template/create/message.txt', context)

        user.email_user(subject, message)
        return redirect('account:user_create_done')

# ユーザ仮登録完了
class UserCreateDone(generic.TemplateView):
    template_name = 'account/user_create_done.html'

# メール内URLアクセス後のユーザー本登録
class UserCreateComplete(generic.TemplateView):
    template_name = 'account/user_create_complete.html'
    timeout_seconds = getattr(settings, 'ACTIVATION_TIMEOUT_SECONDS', 60*60*24)  # タイムアウトは1日

    # tokenが正しければ本登録
    def get(self, request, **kwargs):
        token = kwargs.get('token')
        try:
            user_pk = loads(token, max_age=self.timeout_seconds)

        # 期限切れ
        except SignatureExpired:
            return HttpResponseBadRequest()

        # tokenが間違っている
        except BadSignature:
            return HttpResponseBadRequest()

        # tokenは問題なし
        else:
            try:
                user = User.objects.get(pk=user_pk)
            except User.DoesNotExist:
                return HttpResponseBadRequest()
            else:
                if not user.is_active:
                    # 問題なければ本登録とする
                    user.is_active = True
                    user.save()
                    return super().get(request, **kwargs)

        return HttpResponseBadRequest()