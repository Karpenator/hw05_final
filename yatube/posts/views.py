from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Post, Group, Follow
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from .forms import PostForm, CommentForm
from .utils import paginate_page


User = get_user_model()


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.select_related('group').all()
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.post_set.all()
    posts_count = posts.count()
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
        'group': group,
        'posts_count': posts_count
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    posts_count = posts.count()
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(
            user=request.user, author=author
        ):
            following = True
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
        'posts_count': posts_count,
        'author': author,
        'following': following
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comments,
        'form': form
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/post_create.html'
    is_edit = False
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', post.author)
    return render(request, template, {'form': form, 'is_edit': is_edit})


@login_required
def post_edit(request, post_id):
    template = 'posts/post_create.html'
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'is_edit': is_edit,
        'post': post
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(
        request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate_page(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        follow = Follow.objects.filter(user=request.user, author=author)
        if not follow.exists():
            follow = Follow.objects.create(user=request.user, author=author)
            follow.save()
            return redirect('posts:follow_index')
    return redirect('posts:index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect('posts:index')
