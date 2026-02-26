from django.db import models


class Address(models.Model):
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    line3 = models.CharField(max_length=255, blank=True)
    area = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100)
    postcode = models.CharField(max_length=20)
    country = models.CharField(max_length=100)
    company = models.ForeignKey(
        "Company",
        on_delete=models.CASCADE,
        related_name="addresses",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name_plural = "addresses"

    def __str__(self):
        parts = [self.line1, self.city, self.postcode, self.country]
        return ", ".join(p for p in parts if p)


class Company(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)
    main_address = models.OneToOneField(
        Address,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="main_address_of",
    )

    class Meta:
        verbose_name_plural = "companies"

    def __str__(self):
        return self.name


class PortalUser(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    companies = models.ManyToManyField(
        Company,
        through="CompanyUser",
        related_name="users",
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} <{self.email}>"


class CompanyUser(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    user = models.ForeignKey(PortalUser, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("company", "user")

    def __str__(self):
        return f"{self.user} @ {self.company}"


class CompanyRelationship(models.Model):
    RELATIONSHIP_TYPES = [
        ("parent_child", "Parent / Child"),
        ("supplier_customer", "Supplier / Customer"),
    ]

    # Convention:
    #   parent_child      → from_company is the PARENT,   to_company is the CHILD
    #   supplier_customer → from_company is the SUPPLIER, to_company is the CUSTOMER
    from_company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    to_company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_TYPES)

    class Meta:
        unique_together = ("from_company", "to_company", "relationship_type")

    def __str__(self):
        if self.relationship_type == "parent_child":
            return f"{self.from_company} (parent) → {self.to_company} (child)"
        return f"{self.from_company} (supplier) → {self.to_company} (customer)"
