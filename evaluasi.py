from rag import answer

# (pertanyaan, kata kunci yang harus muncul, harus eskalasi?)
TESTS = [
    ("Gimana cara klaim garansi laptop yang layarnya garis-garis?", ["invoice", "service center"], False),
    ("Berapa lama batas waktu return?", ["7 hari"], False),
    ("Berapa harga Teknoku Pro 16?", ["21.499.000"], False),
    ("Promo gajian berlaku sampai kapan?", ["31 oktober"], False),
    ("Apakah garansi mencakup laptop yang jatuh?", ["tidak"], False),
    ("Berapa lama refund diproses?", ["3-5 hari"], False),
    ("Berapa harga iPhone 15?", [], True),
    ("Apakah ada garansi untuk HP?", [], True),
    ("Siapa presiden Indonesia?", [], True),
    ("Ini toko apa sih?", ["tokoteknoku"], False),
    ("TokoTeknoku jual apa aja?", ["laptop"], False),
    ("Siapa owner TokoTeknoku?", ["budi santoso"], False),
    ("Toko kalian ada di mana?", ["surabaya"], False),
    ("Jam buka toko kapan?", ["senin"], False),
    ("Bisa bayar pakai apa saja?", ["transfer"], False),
    ("Berapa lama pengiriman?", ["2-5"], False),
    ("Apa alamat rumah owner kalian?", [], True),
    ("Apakah ada garansi untuk charger?", [], True),
    ("Apakah TokoTeknoku punya cabang di Jakarta?", [], True),
]

ok = 0
for q, kws, must_esc in TESTS:
    ans, esc = answer(q)
    benar = (esc == must_esc) and all(k in ans.lower() for k in kws)
    ok += benar
    print(f"{'BENAR' if benar else 'SALAH'} | esc={esc} | {q}")
    if not benar:
        print("   ->", ans[:200])
print(f"\nAkurasi: {ok}/{len(TESTS)} = {ok/len(TESTS):.0%}")