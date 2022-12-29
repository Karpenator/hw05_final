from django.views.generic import TemplateView


class About(TemplateView):
    template_name = 'about/about.html'


class Tech(TemplateView):
    template_name = 'about/tech.html'
