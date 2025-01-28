from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile, Project, Contribution, Milestone, Reward, BackerProfile
from .models import CreatorProfile
from django.contrib.admin.sites import NotRegistered
from django.core.mail import send_mail
from django.conf import settings
from .models import Project
from .models import Message, ChatReason
from django.contrib import admin, messages
from .models import Message

class MessageInlineAdmin(admin.TabularInline):
    model = Message
    extra = 1
    readonly_fields = ('sender', 'receiver', 'created_at')

class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'content', 'reason', 'parent_message', 'read', 'created_at')
    list_filter = ('reason', 'read', 'sender', 'receiver')
    search_fields = ('content', 'sender__username', 'receiver__username')
    readonly_fields = ('sender', 'receiver', 'created_at', 'parent_message')

    actions = ['mark_as_read', 'respond_to_message']

    inlines = [MessageInlineAdmin]

    def mark_as_read(self, request, queryset):
        queryset.update(read=True)
        self.message_user(request, "Messages marked as read")

    def respond_to_message(self, request, queryset):
        if not request.user.is_superuser:
            self.message_user(request, "Only admins can respond to messages.", messages.ERROR)
            return

        for message in queryset:
            if message.parent_message is None:  # Avoid replying to replies
                reply_content = f"Admin response to {message.sender.username}'s message"
                Message.objects.create(
                    sender=request.user,
                    receiver=message.sender,
                    content=reply_content,
                    parent_message=message,
                    reason=message.reason,
                    read=True
                )
        self.message_user(request, "Admin reply sent to selected messages.")

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        reason_filter = request.GET.get('reason')
        if reason_filter:
            queryset = queryset.filter(reason__id=reason_filter)
        return queryset



admin.site.register(Message, MessageAdmin)
admin.site.register(ChatReason)

class CreatorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'projects_created_count')
    search_fields = ('user__username',)

    def projects_created_count(self, obj):
        return obj.projects_created.count()
    projects_created_count.short_description = 'Number of Projects Created'


class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'first_name', 'last_name', 'wallet_address', 'is_active', 'is_staff', 'is_superuser')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'wallet_address')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('wallet_address',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('wallet_address',)}),
    )


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'wallet_address', 'national_id', 'contact_address', 'created_at', 'updated_at','wallet_verified')
    list_filter = ('role',)
    search_fields = ('user__username', 'role', 'wallet_address')


class BackerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'rewards_claimed_count')
    search_fields = ('user__username',)

    def rewards_claimed_count(self, obj):
        return obj.rewards_claimed.count()
    rewards_claimed_count.short_description = 'Number of Rewards Claimed'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'creator', 'status', 'funding_goal', 'current_funding', 'deadline','total_platform_fee')
    actions = ['approve_project', 'reject_project']

    def approve_project(self, request, queryset):
        """Approve selected projects and send an approval email to the creators."""
        print(f"Approving {queryset.count()} projects...")  # Debug message
        for project in queryset:
            # Update the project status to 'approved'
            project.status = 'approved'
            project.save()

            # Send approval email
            self.send_approval_email(project)

    def reject_project(self, request, queryset):
        """Reject selected projects."""
        for project in queryset:
            project.status = 'rejected'
            project.save()


try:
    admin.site.unregister(Project)
except NotRegistered:
    pass


admin.site.register(Project, ProjectAdmin)

class ContributionAdmin(admin.ModelAdmin):
    list_display = ('project', 'backer', 'amount', 'transaction_hash', 'payment_status', 'verified', 'date', 'platform_fee')
    list_filter = ('payment_status', 'verified', 'project')
    search_fields = ('project__title', 'backer__username', 'transaction_hash')
    actions = ['mark_as_completed', 'mark_as_failed', 'verify_contributions', 'unverify_contributions']

    def mark_as_completed(self, request, queryset):
        """Mark selected contributions as Completed."""
        updated = queryset.update(payment_status='completed')
        self.message_user(request, f"{updated} contribution(s) marked as Completed.")

    def mark_as_failed(self, request, queryset):
        """Mark selected contributions as Failed."""
        updated = queryset.update(payment_status='failed')
        self.message_user(request, f"{updated} contribution(s) marked as Failed.")

    def verify_contributions(self, request, queryset):
        """Verify selected contributions."""
        updated = queryset.update(verified=True, payment_status='completed')
        self.message_user(request, f"{updated} contribution(s) verified.")

    def unverify_contributions(self, request, queryset):
        """Unverify selected contributions."""
        updated = queryset.update(verified=False, payment_status='pending')
        self.message_user(request, f"{updated} contribution(s) marked as Unverified.")

    mark_as_completed.short_description = "Mark selected contributions as Completed"
    mark_as_failed.short_description = "Mark selected contributions as Failed"
    verify_contributions.short_description = "Verify selected contributions"
    unverify_contributions.short_description = "Unverify selected contributions"
try:
    admin.site.unregister(Contribution)
except NotRegistered:
    pass


# Milestone Admin
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('project', 'title', 'target_amount', 'completed', 'date_created')
    list_filter = ('project', 'completed')
    search_fields = ('project__title', 'title')
#admin.site.unregister(Reward)
# Reward Admin
class RewardAdmin(admin.ModelAdmin):
    list_display = ('project', 'reward_name', 'reward_amount', 'reward_description')
    search_fields = ('reward_name', 'project__title')
    list_filter = ('project',)

    def reward_amount(self, obj):
        return f"${obj.amount:,.2f}"

    reward_amount.short_description = 'Amount'




admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(BackerProfile, BackerProfileAdmin)
admin.site.register(Contribution, ContributionAdmin)
admin.site.register(Milestone, MilestoneAdmin)
admin.site.register(Reward, RewardAdmin)
admin.site.register(CreatorProfile, CreatorProfileAdmin)



