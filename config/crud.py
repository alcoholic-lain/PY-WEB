from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView


class ResourceViewMixin(LoginRequiredMixin):
    login_url = reverse_lazy("admin:login")
    resource_name = ""
    page_title = ""
    page_intro = ""
    list_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            resource_name=self.resource_name,
            page_title=self.page_title,
            page_intro=self.page_intro,
            list_url_name=self.list_url_name,
        )
        return context


class ResourceListView(ResourceViewMixin, ListView):
    template_name = "catalogue/list.html"
    create_url_name = ""
    detail_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            create_url_name=self.create_url_name,
            detail_url_name=self.detail_url_name,
        )
        return context


class ResourceDetailView(ResourceViewMixin, DetailView):
    template_name = "catalogue/detail.html"
    detail_fields = ()
    update_url_name = ""
    delete_url_name = ""
    can_update = True
    can_delete = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        details = []
        for field_name, label in self.detail_fields:
            value = getattr(self.object, field_name)
            display = getattr(self.object, f"get_{field_name}_display", None)
            if display:
                value = display()
            elif isinstance(value, bool):
                value = "Oui" if value else "Non"
            details.append((label, value))
        context.update(
            details=details,
            update_url_name=self.update_url_name,
            delete_url_name=self.delete_url_name,
            can_update=self.can_update,
            can_delete=self.can_delete,
        )
        return context


class ResourceFormViewMixin(ResourceViewMixin):
    template_name = "catalogue/form.html"
    form_intro = ""
    cancel_url_name = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            form_intro=self.form_intro,
            cancel_url_name=self.cancel_url_name,
        )
        return context


class ResourceCreateView(ResourceFormViewMixin, CreateView):
    pass


class ResourceUpdateView(ResourceFormViewMixin, UpdateView):
    pass


class ResourceDeleteView(ResourceViewMixin, DeleteView):
    template_name = "catalogue/delete.html"
    delete_warning = ""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["delete_warning"] = self.delete_warning
        return context
