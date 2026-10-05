from datetime import timedelta
from django.test import RequestFactory, TestCase
from django.utils import timezone
from django.utils.text import slugify

from .invoice_services import create_invoice, update_invoice
from .models import BlogPost, Invoice, InvoiceHistory
from .views import blog
from django.contrib.auth import get_user_model


class BlogSchedulingTests(TestCase):
    def test_scheduled_post_publishes_when_publish_time_has_arrived(self):
        post = BlogPost.objects.create(
            title="Scheduled Post",
            slug="scheduled-post",
            excerpt="Example excerpt",
            content_markdown="Example content",
            status="scheduled",
            published_at=timezone.now() - timedelta(hours=1),
        )

        request = RequestFactory().get("/blog/")
        response = blog(request)

        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.status, "published")
        self.assertTrue(BlogPost.objects.published().filter(pk=post.pk).exists())


class BlogSitemapTests(TestCase):
    def create_post(self, number, **overrides):
        title = overrides.pop("title", f"Sitemap Post {number}")
        return BlogPost.objects.create(
            title=title,
            slug=overrides.pop("slug", f"legacy-post-{number}"),
            excerpt="Example excerpt",
            content_markdown="Example content",
            status="published",
            published_at=timezone.now() - timedelta(minutes=number),
            **overrides,
        )

    def test_sitemap_uses_the_same_direct_200_urls_as_all_blog_pages(self):
        # 43 posts exercise the five pages currently exposed by the public API.
        posts = [self.create_post(number) for number in range(1, 44)]
        legacy_post = posts[0]
        legacy_post.canonical_url = "https://kehem.com/blog/legacy-post-1"
        legacy_post.save(update_fields=["canonical_url"])

        expected_paths = {
            f"/blog/{slugify(post.title)}/"
            for post in posts
        }

        for page_number, expected_count in ((1, 10), (2, 10), (3, 10), (4, 10), (5, 3)):
            response = self.client.get(f"/blog?page={page_number}&format=json")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.json()["posts"]), expected_count)
            self.assertTrue({item["url"] for item in response.json()["posts"]}.issubset(expected_paths))

        sitemap_response = self.client.get("/sitemap.xml", HTTP_HOST="kehem.com")
        self.assertEqual(sitemap_response.status_code, 200)
        sitemap = sitemap_response.content.decode()
        self.assertNotIn(legacy_post.canonical_url, sitemap)

        for path in expected_paths:
            self.assertIn(f"https://kehem.com{path}", sitemap)
            self.assertEqual(self.client.get(path, HTTP_HOST="kehem.com").status_code, 200)

        detail_response = self.client.get(legacy_post.get_absolute_url(), HTTP_HOST="kehem.com")
        self.assertContains(
            detail_response,
            f"https://kehem.com{legacy_post.get_absolute_url()}",
        )
        self.assertNotContains(detail_response, legacy_post.canonical_url)


class InvoiceManagementTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create(
            email="invoice-staff@kehem.com",
            first_name="Invoice",
            last_name="Staff",
            Mobile="+8801700000000",
            is_active=True,
            is_staff=True,
        )
        self.payload = {
            "customer_name": "Nordic Studio",
            "customer_company": "Nordic Studio AB",
            "invoice_date": "2026-07-29",
            "due_date": "2026-08-12",
            "currency": "BDT",
            "status": "draft",
            "shipping": "10",
            "service_charge": "0",
            "extra_cost": "0",
            "additional_discount": "0",
            "paid_amount": "50",
            "items": [
                {
                    "description": "Interface design",
                    "quantity": "2",
                    "unit_price": "100",
                    "discount_percent": "10",
                    "tax_percent": "5",
                }
            ],
        }

    def test_invoice_number_and_totals_are_calculated_server_side(self):
        invoice = create_invoice(self.payload, self.user)

        self.assertEqual(invoice.invoice_number, "INV-20260729-0001")
        self.assertEqual(str(invoice.subtotal), "200.00")
        self.assertEqual(str(invoice.discount_total), "20.00")
        self.assertEqual(str(invoice.tax_total), "9.00")
        self.assertEqual(str(invoice.grand_total), "199.00")
        self.assertEqual(str(invoice.balance), "149.00")

    def test_edit_creates_an_immutable_history_snapshot(self):
        invoice = create_invoice(self.payload, self.user)
        changed_payload = {**self.payload, "customer_name": "Updated Customer"}

        updated = update_invoice(invoice, changed_payload, self.user)

        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.customer_name, "Updated Customer")
        history = InvoiceHistory.objects.get(invoice=updated, version=1)
        self.assertEqual(history.snapshot["customer_name"], "Nordic Studio")

    def test_read_only_staff_cannot_create_invoice(self):
        self.user.staff_role = "Read Only"
        self.user.save(update_fields=["staff_role"])
        self.client.force_login(self.user)

        response = self.client.post(
            "/api/invoices/",
            data=self.payload,
            content_type="application/json",
            HTTP_HOST="kehem.com",
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Invoice.objects.count(), 0)
