from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.fields import GenericForeignKey
from django_comments.models import Comment
from django.contrib.contenttypes.models import ContentType



class Category(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subcategories',
        help_text="Parent Category for hierarchical categorization."
    )

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    
class DataType(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='sub_data_types',
        help_text="Parent DataType for hierarchical categorization."
    )

    def __str__(self):
        return self.name

class DataSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    data_type = models.ForeignKey(DataType, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    comments = GenericRelation(Comment)
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')


    class Meta:
        ordering = ['-created_at']
        verbose_name = "Data Submission"
        verbose_name_plural = "Data Submissions"

    def __str__(self):
        return self.title

class Evidence(models.Model):
    submission = models.ForeignKey(
        'DataSubmission',
        on_delete=models.CASCADE,
        related_name='evidences'
    ) 
    user = models.ForeignKey(
        User,  
        on_delete=models.CASCADE
    )
    description = models.TextField(
        help_text="Provide a brief description of the evidence."
    )
    link = models.URLField(
        blank=True,
        null=True,
        help_text="Optional URL link to the evidence."
    )
    document = models.FileField(
        upload_to='evidences/',
        blank=True,
        null=True,
        help_text="Optional file upload for the evidence."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the evidence was created."
    )
    
    voters = models.ManyToManyField(User, related_name='voted_evidences', blank=True)
    
    comments = GenericRelation(Comment)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True)
    object_id = models.PositiveIntegerField(null=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        verbose_name = "Evidence"
        verbose_name_plural = "Evidences"
        ordering = ['-created_at']
        unique_together = ('submission', 'link', 'document', 'description')

    def __str__(self):
        return f"Evidence for '{self.submission.title}'"

    def add_vote(self, user):
        """Allow users to vote on this evidence."""
        if not self.voters.filter(id=user.id).exists():
            self.voters.add(user)

    def remove_vote(self, user):
        """Allow users to remove their vote."""
        if self.voters.filter(id=user.id).exists():
            self.voters.remove(user)

    def total_votes(self):
        """Return the total number of votes."""
        return self.voters.count()


class Verification(models.Model):
    submission = models.ForeignKey(
        'DataSubmission',
        on_delete=models.CASCADE,
        related_name='verifications'
    )
    user = models.ForeignKey(
        User,  
        on_delete=models.CASCADE
    )
    vote = models.BooleanField(
        help_text="Indicates if the data is valid (True) or invalid (False)."
    )
    staked_tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Amount of tokens staked on the verification."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the verification was created."
    )
    
    is_disputed = models.BooleanField(
        default=False,
        help_text="Indicates if the verification is disputed."
    )
    experts = models.ManyToManyField(
        User,
        related_name='expert_verifications',
        blank=True,
        help_text="Experts assigned to review the verification in case of dispute."
    )
    expert_votes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stores votes from experts. Format: {'expert_id': vote}."
    )
    expert_staked_tokens = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="Total tokens staked by experts."
    )
    resolution_status = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="The final resolution status after expert review, e.g., 'Valid', 'Invalid', or 'Undecided'."
    )

    class Meta:
        verbose_name = "Verification"
        verbose_name_plural = "Verifications"
        ordering = ['-created_at']

    def __str__(self):
        return f"Verification on '{self.submission.title}'"

    def add_expert_vote(self, expert, vote, tokens):
        """Add an expert's vote to the expert_votes and update the expert_staked_tokens."""
        self.expert_votes[expert.id] = vote
        self.expert_staked_tokens += tokens
        self.save()


class ReputationChange(models.Model):
    user = models.ForeignKey(
        User,  
        on_delete=models.CASCADE
    )
    change = models.IntegerField(
        help_text="Amount of reputation points changed. Positive for gains, negative for losses."
    )
    reason = models.TextField(
        help_text="Description of the reason for the reputation change."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when the reputation change was recorded."
    )

    class Meta:
        verbose_name = "Reputation Change"
        verbose_name_plural = "Reputation Changes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Reputation change for {self.user.username}: {self.change} points"


class ExternalUser(models.Model):
    """Model to store data about external users fetched from the API."""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    mpxr = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text="mpxr value fetched from the external API."
    )

    def __str__(self):
        return f"External Data for {self.user.username}: mpxr {self.mpxr}"
