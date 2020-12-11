import gnupg


class FileDecryptError(Exception):
    pass


def decrypt_pgp(input_filepath: str, output_filepath: str, private_key: str, passphrase: str) -> str:
    """Decrypt PGP file using private key and passphrase."""
    gpg = gnupg.GPG()
    gpg.import_keys(private_key)

    with open(input_filepath, "rb") as encrypted_f:
        result = gpg.decrypt_file(encrypted_f,
                                  passphrase=passphrase,
                                  output=output_filepath,
                                  extra_args=["--ignore-mdc-error"])
        if result.ok:
            return output_filepath
        else:
            raise FileDecryptError(result.stderr)


def encrypt_pgp(input_filepath: str, output_filepath: str, public_key: str) -> str:
    """Encrypt PGP file using public key."""
    gpg = gnupg.GPG()
    key = gpg.import_keys(public_key)

    recipient = key.results[0]["fingerprint"]

    with open(input_filepath, "rb") as f:
        result = gpg.encrypt_file(file=f, recipients=[recipient], output=output_filepath, always_trust=True)
        if result.ok:
            return output_filepath
        else:
            raise FileDecryptError(result.stderr)
