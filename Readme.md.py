# 📨 Pico W - MQTT Komut Sözleşmesi, ACK ve Sonuç Yönetimi

Raspberry Pi Pico W için tasarlanmış, komut onay (ACK) ve işlem sonucu (RESULT) mesaj süreçlerini ayrıştıran güvenilir MicroPython haberleşme altyapısı.

## 🚀 Özellikler

- **İki Aşamalı Mesaj Onayı:** Komut alındığında anında onay (`command-ack`), donanım işlemi bittiğinde ise nihai durum (`command-result`) yayınlanır.
- **Mükerrer Komut (Duplicate) Engelleme:** İstemciden gelen `clientRequestId` değerlerini bellekte tutarak aynı komutun birden fazla kez çalıştırılmasını engeller.
- **İzlenebilirlik:** Mobil uygulama veya sunucu tarafında her komutun durumunu uçtan uca takip etmeyi sağlar.

## 📋 Kullanılan Topic Yapısı

- `.../command`: Gelen çalıştırma talimatları.
- `.../command-ack`: Komut kabul/ret bildirimi (`accepted` / `rejected`).
- `.../command-result`: Komut çalışma sonucu (`success` / `failure`).

## 🛠️ Gereksinimler

- Donanım: Raspberry Pi Pico W, Waveshare Pico-Relay-B
- Yazılım: MicroPython (v1.20.0+)