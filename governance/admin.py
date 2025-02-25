"""
Admin configuration for the governance app.
"""

from django.contrib import admin
from .models import Proposal, Vote, ProposalComment, GovernanceToken, Guardian


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    """Admin configuration for Proposal model."""
    
    list_display = (
        'id', 'title', 'proposer', 'status', 'created_at',
        'discussion_start_time', 'voting_start_time', 'voting_end_time'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'description', 'proposer__username')
    readonly_fields = (
        'created_at', 'updated_at', 'discussion_start_time',
        'voting_start_time', 'voting_end_time', 'execution_time',
        'total_votes_for', 'total_votes_against', 'total_voting_power'
    )
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'rationale', 'implementation_details', 'timeline')
        }),
        ('Metadata', {
            'fields': ('proposer', 'status', 'created_at', 'updated_at')
        }),
        ('Timeline', {
            'fields': ('discussion_start_time', 'voting_start_time', 'voting_end_time', 'execution_time')
        }),
        ('Voting Results', {
            'fields': ('total_votes_for', 'total_votes_against', 'total_voting_power')
        }),
        ('External Content', {
            'fields': ('content_document_id',)
        }),
    )


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    """Admin configuration for Vote model."""
    
    list_display = ('id', 'proposal', 'voter', 'vote_count', 'vote_cost', 'is_for', 'created_at')
    list_filter = ('is_for', 'created_at')
    search_fields = ('proposal__title', 'voter__username')
    readonly_fields = ('vote_cost', 'created_at')


@admin.register(ProposalComment)
class ProposalCommentAdmin(admin.ModelAdmin):
    """Admin configuration for ProposalComment model."""
    
    list_display = ('id', 'proposal', 'author', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('proposal__title', 'author__username', 'content')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(GovernanceToken)
class GovernanceTokenAdmin(admin.ModelAdmin):
    """Admin configuration for GovernanceToken model."""
    
    list_display = ('id', 'holder', 'balance', 'locked_until', 'delegated_to')
    list_filter = ('locked_until',)
    search_fields = ('holder__username', 'delegated_to__username')
    readonly_fields = ('locked_until',)


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    """Admin configuration for Guardian model."""
    
    list_display = ('id', 'user', 'term_start_date', 'term_end_date', 'is_active')
    list_filter = ('is_active', 'term_start_date', 'term_end_date')
    search_fields = ('user__username',)
    readonly_fields = ('user', 'term_start_date', 'term_end_date', 'is_active') 