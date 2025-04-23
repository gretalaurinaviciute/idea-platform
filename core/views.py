from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserRegisterForm, IdeaForm, ProfileForm, CustomPasswordChangeForm, PortfolioForm, ReviewForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash, login
from django.contrib import messages
from datetime import datetime
from django.db.models import Q, Avg
from .models import Idea, IdeaFile, Category, User, SavedIdea, Review, Message
from django.utils.translation import gettext as _
from django.utils.translation import activate
import os
import magic


ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.txt', '.png', '.jpg', '.jpeg']
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def set_language(request):
    lang_code = request.GET.get('language')
    if lang_code:
        request.session['django_language'] = lang_code
        activate(lang_code)
    next_url = request.META.get('HTTP_REFERER', '/')
    if not next_url.startswith(f'/{lang_code}/'):
        next_url = f'/{lang_code}/'
    return redirect(next_url)


def home(request):
    if request.user.is_authenticated:
        return redirect('search')
    return redirect('login')


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.type = form.cleaned_data.get('user_type')

            if user.type == 'SPECIALIST':
                user.category = form.cleaned_data.get('category')
                user.skills = ", ".join([
                    form.cleaned_data.get('skills_1', ''),
                    form.cleaned_data.get('skills_2', ''),
                    form.cleaned_data.get('skills_3', ''),
                ])
                user.experience = int(form.cleaned_data.get('experience', 0))

            elif user.type == 'PROPOSER':
                user.category = form.cleaned_data.get('category')

            user.agreed_to_terms_at = datetime.now()

            user.save()
            login(request, user)  # log in user automaticaly
            return redirect('home')

        else:
            return render(request, 'users/register.html', {'form': form})


    else:
        form = UserRegisterForm()

    return render(request, 'users/register.html', {'form': form})


def terms(request):
    return render(request, "users/terms.html")


@login_required
def my_profile(request):
    user = request.user
    form = ProfileForm(instance=user)
    password_form = CustomPasswordChangeForm(user)
    portfolio_form = PortfolioForm()

    received_reviews = user.received_reviews.select_related("reviewer").order_by("-created_at")
    avg_rating = received_reviews.aggregate(Avg("rating"))["rating__avg"]
    avg_rating = round(avg_rating, 1) if avg_rating else None

    if request.method == "POST":
        if "update_profile" in request.POST:
            form = ProfileForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                return redirect("profile")

        elif "update_password" in request.POST:
            password_form = CustomPasswordChangeForm(user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # keep user logged in
                messages.success(request, _("Password updated successfully!"))
                return redirect("profile")
            else:
                messages.error(request, _("Please correct the error above."))

        elif "add_portfolio" in request.POST:
            portfolio_form = PortfolioForm(request.POST, request.FILES)
            if portfolio_form.is_valid():
                portfolio = portfolio_form.save(commit=False)
                portfolio.user = request.user
                portfolio.save()
                messages.success(request, _("Image uploaded!"))
                return redirect("profile")

    portfolios = request.user.portfolios.all()

    return render(request, "users/profile.html", {
        "form": form,
        "password_form": password_form,
        "portfolio_form": portfolio_form,
        "portfolios": portfolios,
        "show_messages": True,
        "reviews": received_reviews,
        "avg_rating": avg_rating,
    })


@login_required
def my_ideas(request):
    if request.user.type != "PROPOSER":
        return redirect("home")

    ideas = Idea.objects.filter(user=request.user)
    return render(request, "users/my_ideas.html", {
        "ideas": ideas,
        "show_messages": True
    })


@login_required
def post_idea(request):
    if request.user.type != "PROPOSER":
        return redirect("home")

    if request.method == "POST":
        form = IdeaForm(request.POST, request.FILES)
        files = request.FILES.getlist("files")

        if form.is_valid():
            category = form.cleaned_data.get("category")
            new_category_name = form.cleaned_data.get("new_category")

            if new_category_name:
                category, created = Category.objects.get_or_create(
                    name=new_category_name,
                    defaults={"status": "PENDING", "suggested_by": request.user}
                )

                if created:
                    messages.success(request, _("New category '%(name)s' created and marked as PENDING.") % {"name": new_category_name})

            if category.status == "PENDING":
                messages.warning(request, _("Your idea has been saved, but the category is pending approval."))

            idea = form.save(commit=False)
            idea.user = request.user
            idea.category = category
            idea.save()

            mime = magic.Magic(mime=True)

            for file in files:
                ext = os.path.splitext(file.name)[1].lower()

                if ext not in ALLOWED_EXTENSIONS:
                    messages.error(request, _("File type %(ext)s is not allowed.") % {"ext": ext})
                    continue  # skip this file

                if file.size > MAX_FILE_SIZE:
                    messages.error(request, _("%(file)s exceeds the 5MB limit.") % {"file": file.name})
                    continue  # skip this file

                file_mime = mime.from_buffer(file.read(1024))
                file.seek(0)

                mime_whitelist = {
                    '.pdf': ['application/pdf'],
                    '.jpg': ['image/jpeg'],
                    '.jpeg': ['image/jpeg'],
                    '.png': ['image/png'],
                    '.txt': ['text/plain'],
                    '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'application/zip']
                }

                # validation
                allowed_mimes = mime_whitelist.get(ext, [])
                if file_mime not in allowed_mimes:
                    messages.error(request, _("%(file)s has unsupported MIME type (%(mime)s) for extension %(ext)s.") % {
                        "file": file.name, "mime": file_mime, "ext": ext
                    })
                    continue

                IdeaFile.objects.create(idea=idea, file=file)

            return redirect("my_ideas")

    else:
        form = IdeaForm()

    return render(request, "users/post_idea.html", {"form": form})


@login_required
def edit_idea(request, idea_id):
    idea = get_object_or_404(Idea, id=idea_id, user=request.user)

    if request.method == "POST":
        form = IdeaForm(request.POST, request.FILES, instance=idea)
        files = request.FILES.getlist("files")
        remove_files = request.POST.getlist("remove_files")

        if form.is_valid():
            updated_idea = form.save(commit=False)
            updated_idea.save()

            IdeaFile.objects.filter(id__in=remove_files).delete()

            mime = magic.Magic(mime=True)

            for file in files:
                ext = os.path.splitext(file.name)[1].lower()

                if ext not in ALLOWED_EXTENSIONS:
                    messages.error(request, _("File type %(ext)s is not allowed.") % {"ext": ext})
                    continue  # skip this file

                if file.size > MAX_FILE_SIZE:
                    messages.error(request, _("%(file)s exceeds the 5MB limit.") % {"file": file.name})
                    continue  # skip this file

                file_mime = mime.from_buffer(file.read(1024))
                file.seek(0)
                # acceptable MIME types for extensions
                mime_whitelist = {
                    '.pdf': ['application/pdf'],
                    '.jpg': ['image/jpeg'],
                    '.jpeg': ['image/jpeg'],
                    '.png': ['image/png'],
                    '.txt': ['text/plain'],
                    '.docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                              'application/zip']
                }

                allowed_mimes = mime_whitelist.get(ext, [])
                if file_mime not in allowed_mimes:
                    messages.error(request, _("❌ %(file)s has unsupported MIME type (%(mime)s) for extension %(ext)s.") % {
                        "file": file.name, "mime": file_mime, "ext": ext
                    })
                    continue

                IdeaFile.objects.create(idea=updated_idea, file=file)

            messages.success(request, _("Idea updated successfully!"))
            return redirect("my_ideas")

    else:
        form = IdeaForm(instance=idea)

    return render(request, "users/post_idea.html", {"form": form, "editing": True, "idea": idea})


@login_required
def delete_idea(request, idea_id):
    idea = get_object_or_404(Idea, id=idea_id, user=request.user)

    if request.method == "POST":
        idea.delete()
        messages.success(request, _("Idea deleted successfully!"))
        return redirect("my_ideas")

    return render(request, "users/delete_idea.html", {"idea": idea})


@login_required
def search(request):
    user = request.user
    query = request.GET.get("q")
    category = request.GET.get("category")
    skill = request.GET.get("skill")
    if user.type == "PROPOSER":
        specialists = User.objects.filter(type="SPECIALIST")
    elif user.type == "SPECIALIST":
        specialists = User.objects.filter(type="PROPOSER")
    ideas = Idea.objects.all()

    if query:
        if user.type == "PROPOSER":
            specialists = specialists.filter(
                Q(username__icontains=query) |
                Q(description__icontains=query)
            )
        elif user.type == "SPECIALIST":
            ideas = ideas.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )
            specialists = specialists.filter(
                Q(username__icontains=query) |
                Q(description__icontains=query)
            )

    if category:
        if user.type == "SPECIALIST":
            ideas = ideas.filter(category__id=category)
        specialists = specialists.filter(category__id=category)

    if skill:
        specialists = specialists.filter(skills__icontains=skill)

    context = {
        "user_type": user.type,
        "query": query or "",
        "selected_category": int(category) if category else None,
        "selected_skill": skill or "",
        "categories": Category.objects.filter(status='APPROVED'),
        "specialists": specialists if user.type in ["PROPOSER", "SPECIALIST"] else None,
        "ideas": ideas if user.type == "SPECIALIST" else None,
    }

    return render(request, "users/search.html", context)


@login_required
def view_idea(request, idea_id):
    idea = get_object_or_404(Idea, pk=idea_id)
    is_saved = SavedIdea.objects.filter(user=request.user, idea=idea).exists()
    return render(request, 'users/view_idea.html', {'idea': idea, 'is_saved': is_saved})


@login_required
def save_idea(request, idea_id):
    idea = get_object_or_404(Idea, id=idea_id)
    SavedIdea.objects.get_or_create(user=request.user, idea=idea)
    return redirect('view_idea', idea_id=idea.id)


@login_required
def saved_ideas_list(request):
    saved = SavedIdea.objects.filter(user=request.user).select_related("idea", "idea__category")
    return render(request, "users/saved_ideas.html", {"saved_ideas": saved})


@login_required
def toggle_saved_idea(request, idea_id):
    idea = get_object_or_404(Idea, id=idea_id)
    saved_entry = SavedIdea.objects.filter(user=request.user, idea=idea).first()

    if saved_entry:
        saved_entry.delete()
    else:
        SavedIdea.objects.create(user=request.user, idea=idea)

    return redirect(request.META.get('HTTP_REFERER', 'search'))


@login_required
def view_user_profile(request, user_id):
    profile_user = get_object_or_404(User, id=user_id)

    if profile_user.type not in ['SPECIALIST', 'PROPOSER']:
        return redirect('search')

    if profile_user == request.user:
        review = None
        form = None
    else:
        try:
            review = Review.objects.get(reviewer=request.user, reviewed_user=profile_user)
        except Review.DoesNotExist:
            review = None

        if request.method == "POST" and "submit_review" in request.POST:
            form = ReviewForm(request.POST, instance=review)
            if form.is_valid():
                new_review = form.save(commit=False)
                new_review.reviewer = request.user
                new_review.reviewed_user = profile_user
                new_review.save()
                messages.success(request, _("your review has been submitted!"))
                return redirect("view_user_profile", user_id=profile_user.id)
        else:
            form = ReviewForm(instance=review)

    is_proposer = profile_user.type == 'PROPOSER'
    ideas = profile_user.ideas.all() if is_proposer else None
    has_ideas = ideas.exists() if ideas else False
    reviews = profile_user.received_reviews.select_related("reviewer").order_by('-created_at')

    avg_rating = profile_user.received_reviews.aggregate(Avg("rating"))["rating__avg"]
    avg_rating = round(avg_rating, 1) if avg_rating else None

    return render(request, 'users/view_user_profile.html', {
        'profile_user': profile_user,
        'is_proposer': is_proposer,
        'has_ideas': has_ideas,
        'ideas': ideas,
        'form': form,
        'existing_review': review,
        'reviews': reviews,
        'show_messages': True,
        'avg_rating': avg_rating,
    })


@login_required
def inbox(request):
    user = request.user

    messages = Message.objects.filter(Q(sender=user) | Q(receiver=user))

    conversation_users = messages.values('sender', 'receiver')

    conversation_partners_ids = set()
    for entry in conversation_users:
        if entry['sender'] != user.id:
            conversation_partners_ids.add(entry['sender'])
        if entry['receiver'] != user.id:
            conversation_partners_ids.add(entry['receiver'])

    conversations = []
    for partner_id in conversation_partners_ids:
        last_msg = Message.objects.filter(
            Q(sender=user, receiver_id=partner_id) | Q(sender_id=partner_id, receiver=user)
        ).order_by('-timestamp').first()

        if last_msg:
            conversations.append(last_msg)

    conversations.sort(key=lambda x: x.timestamp, reverse=True)

    return render(request, 'users/inbox.html', {
        'conversations': conversations
    })


@login_required
def conversations(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other_user) |
        Q(sender=other_user, receiver=request.user)
    )

    messages.filter(receiver=request.user, is_read=False).update(is_read=True)

    if request.method == "POST":
        Message.objects.create(
            sender=request.user,
            receiver=other_user,
            body=request.POST.get('body', '').strip()
        )
        return redirect('conversations', user_id=user_id)

    return render(request, 'users/conversations.html', {
        'messages': messages,
        'other_user': other_user,
    })

