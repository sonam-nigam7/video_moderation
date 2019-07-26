from django.contrib import admin

from .models import Mod

class ModAdmin(admin.ModelAdmin):
    # ...
    list_display = ('name', 'pub_date', 'status', 'url')
    list_filter = ('status',)
    change_form_template = "/Users/sonam.nigam/project/video_moderation/project/video_moderation/mod/templates/change_list.html"

    def response_change(self, request, obj):
        import pdb;pdb.set_trace()
        if "_make-unique" in request.POST:
            matching_names_except_this = self.get_queryset(request).filter(name=obj.name).exclude(pk=obj.id)
            matching_names_except_this.delete()
            obj.is_unique = True
            obj.save()
            self.message_user(request, "This villain is now unique")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)

admin.site.register(Mod, ModAdmin)