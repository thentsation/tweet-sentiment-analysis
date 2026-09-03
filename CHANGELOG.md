# CHANGELOG

<!-- version list -->

## v1.2.3 (2026-09-03)

### Bug Fixes

- Preserve trailing newline when writing SSH key from secret
  ([`daa31d1`](https://github.com/thentsation/tweet-sentiment-analysis/commit/daa31d11d612f9ea93a033c1fddec03c811860fc))


## v1.2.2 (2026-09-03)

### Bug Fixes

- **audit**: Ignore specific vulnerability in pip-audit checks
  ([`ec6e6fe`](https://github.com/ntsation/tweet-sentiment-analysis/commit/ec6e6feb24ac3dd076b1baa51834cf0a26cb3920))

### Chores

- **deps**: Bump minio from 7.2.9 to 7.2.20 in /config
  ([`a97ae88`](https://github.com/ntsation/tweet-sentiment-analysis/commit/a97ae88fda61031dba259cc49ccd7cf41d5ce291))


## v1.2.1 (2026-08-31)

### Bug Fixes

- **storage**: Update datetime import to use UTC for consistency
  ([`f9a094b`](https://github.com/ntsation/tweet-sentiment-analysis/commit/f9a094b8356a00c0a06c077ea9e34ba1d86db4ec))


## v1.2.0 (2026-08-31)

### Chores

- **ci**: Bump docker/login-action from 3 to 4
  ([`b7c039e`](https://github.com/ntsation/tweet-sentiment-analysis/commit/b7c039e07d309e2652119dc85032ed762f3e820f))

- **ci**: Bump docker/setup-qemu-action from 3 to 4
  ([`bcf5a73`](https://github.com/ntsation/tweet-sentiment-analysis/commit/bcf5a735efe7e7540b149e31e0950c8feb04afb0))

- **ci**: Bump python-semantic-release/python-semantic-release
  ([`1fdc19b`](https://github.com/ntsation/tweet-sentiment-analysis/commit/1fdc19b836c4581f7fb24df19f5b944e90ca5f44))

- **deps**: Bump ruff from 0.16.3 to 0.16.4 in /config
  ([`f860ab0`](https://github.com/ntsation/tweet-sentiment-analysis/commit/f860ab072f89bc676cc747f9f30864172bff615d))

- **deps**: Bump ruff from 0.16.4 to 0.16.5 in /config
  ([`703afa6`](https://github.com/ntsation/tweet-sentiment-analysis/commit/703afa668db1450217e0bf9bd4e2b85050060774))

### Features

- **docker**: Add nginx configuration for serving reports
  ([`5d76d5b`](https://github.com/ntsation/tweet-sentiment-analysis/commit/5d76d5b7c597ee9dc6c721bfa3fce7da7cbee39d))


## v1.1.0 (2026-08-22)

### Features

- **ci**: Notify portfolio to rebuild on push to main
  ([`7810346`](https://github.com/ntsation/tweet-sentiment-analysis/commit/78103464b91d9d699d93ecb13890a0cd95e5f69d))


## v1.0.2 (2026-08-22)

### Bug Fixes

- Atualiza skip-dirs do trivy para python 3.14
  ([`379a59d`](https://github.com/ntsation/tweet-sentiment-analysis/commit/379a59ddf204defeb5292128a3c71f6d8ee86c43))

- Remove ensurepip da imagem para eliminar wheel vulneravel do pip
  ([`13c9e06`](https://github.com/ntsation/tweet-sentiment-analysis/commit/13c9e06656d2ccd88bf4ebe27d236b8546ccf9d6))


## v1.0.1 (2026-08-22)

### Bug Fixes

- **ci**: Update trivy skip-dirs to match python 3.14 base image
  ([`22fc8c6`](https://github.com/ntsation/tweet-sentiment-analysis/commit/22fc8c64128c1d55babb05be086c344448a2da61))

### Chores

- **ci**: Add PR and issue templates
  ([`740b44f`](https://github.com/ntsation/tweet-sentiment-analysis/commit/740b44f747b45a10f6b568f93e599140c6b2d831))

- **ci**: Bump docker/build-push-action from 6 to 7
  ([`905acce`](https://github.com/ntsation/tweet-sentiment-analysis/commit/905acce37b2783e7d9dd2e1c5e01395a512c9de5))

- **ci**: Bump docker/login-action from 3 to 4
  ([`815b9d4`](https://github.com/ntsation/tweet-sentiment-analysis/commit/815b9d4f9b64ca77ce1717a83c27bc87a54951e2))

- **ci**: Bump docker/metadata-action from 5 to 6
  ([`e9f0a03`](https://github.com/ntsation/tweet-sentiment-analysis/commit/e9f0a03c67de697d2482108149827aed53d7e857))

- **deps**: Bump python from 3.12-slim to 3.14-slim in /docker
  ([`c98e25a`](https://github.com/ntsation/tweet-sentiment-analysis/commit/c98e25a61b2c44626aa4c6ef1b522b776213b58e))


## v1.0.0 (2026-08-22)

- Initial Release
