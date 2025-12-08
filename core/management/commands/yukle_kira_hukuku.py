# core/management/commands/yukle_kira_hukuku.py

from django.core.management.base import BaseCommand
from core.models import KanunMaddesi, HukukKategori

class Command(BaseCommand):
    help = 'Kira Hukuku verilerini veritabanına yükler'

    def handle(self, *args, **kwargs):
        # 1. Kategoriyi Oluştur veya Getir
        kategori, created = HukukKategori.objects.get_or_create(
            slug="kira-hukuku",
            defaults={
                "isim": "Kira Hukuku",
                "ikon": "🏠",
                "aciklama": "Konut ve çatılı işyeri kiraları, tahliye ve tespit davaları.",
                "ai_talimati": "Sen uzman bir kira hukuku avukatısın. Sadece Türk Borçlar Kanunu ve Yargıtay içtihatlarına göre cevap ver.",
                "aktif_mi": True
            }
        )

        # 2. Kanun Maddeleri (Örnek Veri Seti - TBK)
        kanunlar = [
            {
                "kanun_adi": "Türk Borçlar Kanunu",
                "madde_no": "Madde 299",
                "icerik": "Kira sözleşmesi, kiraya verenin bir şeyin kullanılmasını veya kullanmayla birlikte ondan yararlanılmasını kiracıya bırakmayı, kiracının da buna karşılık kararlaştırılan kira bedelini ödemeyi üstlendiği sözleşmedir."
            },
            {
                "kanun_adi": "Türk Borçlar Kanunu",
                "madde_no": "Madde 344",
                "icerik": "Tarafların yenilenen kira dönemlerinde uygulanacak kira bedeline ilişkin anlaşmaları, bir önceki kira yılında tüketici fiyat endeksindeki oniki aylık ortalamalara göre değişim oranını geçmemek koşuluyla geçerlidir."
            },
            {
                "kanun_adi": "Türk Borçlar Kanunu",
                "madde_no": "Madde 347",
                "icerik": "Konut ve çatılı işyeri kiralarında kiracı, belirli süreli sözleşmelerin süresinin bitiminden en az onbeş gün önce bildirimde bulunmadıkça, sözleşme aynı koşullarla bir yıl için uzatılmış sayılır. Kiraya veren, sözleşme süresinin bitimine dayanarak sözleşmeyi sona erdiremez. Ancak, on yıllık uzama süresi sonunda kiraya veren, bu süreyi izleyen her uzama yılının bitiminden en az üç ay önce bildirimde bulunmak koşuluyla, herhangi bir sebep göstermeksizin sözleşmeye son verebilir."
            },
            {
                "kanun_adi": "Türk Borçlar Kanunu",
                "madde_no": "Madde 350 (İhtiyaç Nedeniyle Tahliye)",
                "icerik": "Kiraya veren, kiralananı kendisi, eşi, altsoyu, üstsoyu veya kanun gereği bakmakla yükümlü olduğu diğer kişiler için konut ya da işyeri gereksinimi sebebiyle kullanma zorunluluğu varsa, belirli süreli sözleşmelerde sürenin sonunda, belirsiz süreli sözleşmelerde kiraya ilişkin genel hükümlere göre fesih dönemine ve fesih bildirimi için öngörülen sürelere uyularak belirlenecek tarihte açacağı dava ile sona erdirebilir."
            },
            {
                "kanun_adi": "Türk Borçlar Kanunu",
                "madde_no": "Madde 351 (Yeni Malik İhtiyacı)",
                "icerik": "Kiralananı sonradan edinen kişi, onu kendisi, eşi, altsoyu, üstsoyu veya kanun gereği bakmakla yükümlü olduğu diğer kişiler için konut veya işyeri gereksinimi sebebiyle kullanma zorunluluğu varsa, edinme tarihinden başlayarak bir ay içinde durumu kiracıya yazılı olarak bildirmek koşuluyla, kira sözleşmesini altı ay sonra açacağı bir dava ile sona erdirebilir."
            },
             {
                "kanun_adi": "Yargıtay İçtihadı",
                "madde_no": "3. Hukuk Dairesi - Tahliye Taahhütnamesi",
                "icerik": "Tahliye taahhütnamesinin geçerli olabilmesi için kira sözleşmesinin düzenlenmesinden sonraki bir tarihte verilmiş olması zorunludur. Sözleşme ile aynı tarihli taahhütnameler, kiracının iradesinin baskı altında olduğu kabul edilerek geçersiz sayılır."
            }
        ]

        # 3. Veritabanına Kaydet
        sayac = 0
        for veri in kanunlar:
            obj, created = KanunMaddesi.objects.get_or_create(
                kategori=kategori,
                kanun_adi=veri["kanun_adi"],
                madde_no=veri["madde_no"],
                defaults={"icerik": veri["icerik"]}
            )
            if created:
                sayac += 1

        self.stdout.write(self.style.SUCCESS(f'✅ Başarılı: {sayac} adet yeni Kira Hukuku maddesi eklendi.'))