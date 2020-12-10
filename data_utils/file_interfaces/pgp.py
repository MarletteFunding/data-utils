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
