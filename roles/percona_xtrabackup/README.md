# Process for Creating and Restoring Backups from Xtradb with Percona Xtrabackup

## Prerequisites

1. Ensure Docker is installed and running on your system.
2. You will need an active instance of MySQL 8.0.
3. Make sure you have the backup file in '.xbstream' format. You can create it using the percona_xtrabackup role using:
```bash
ansible-playbook -i nau-data/envs/development/hosts.ini mysql_xtrabackups.yml --limit XPTO
```

## 1. Unpacking the Backup

Unpacks the `backup.xbstream` file to the specified location.

```bash
docker run --rm --network=host --name percona-xtrabackup --volumes-from xtradb -v /root/xtrabackups:/xtrabackup_backupfiles percona/percona-xtrabackup:8.0.34 /bin/bash -c "cat /xtrabackup_backupfiles/backup.xbstream | xbstream -x -C /xtrabackup_backupfiles"
```

### Options:

- `xbstream -x`: Extracts the contents of the `xbstream` file.
- `-C`: Specifies the target directory for extraction.

## 2. Decompressing the Backup

To decompress the files within the unpacked backup, use the following command. This also removes the original compressed files.

```bash
docker run --rm --network=host --name percona-xtrabackup --volumes-from xtradb -v /root/xtrabackups:/xtrabackup_backupfiles percona/percona-xtrabackup:8.0.34 /bin/bash -c "xtrabackup --decompress --remove-original --target-dir=/xtrabackup_backupfiles"
```

### Options:

- `--decompress`: Decompresses the files in the backup.
- `--remove-original`: Deletes the original compressed files.
- `--target-dir`: Specifies the directory containing the decompressed files.

## 3. Preparing the Backup

This step applies any pending transactions and makes the backup consistent for restoration.

```bash
docker run --rm --network=host --name percona-xtrabackup --volumes-from xtradb -v /root/xtrabackups:/xtrabackup_backupfiles percona/percona-xtrabackup:8.0.34 /bin/bash -c "xtrabackup --prepare --target-dir=/xtrabackup_backupfiles"
```

### Options:

- `--prepare`: Applies pending transactions to the backup.
- `--target-dir`: The directory where the decompressed backup is located.

## 4. Restoring the Backup

Finally, the following command restores the backup to the specified data directory.

```bash
docker run --rm --network=host --name percona-xtrabackup --volumes-from xtradb -v /root/xtrabackups:/xtrabackup_backupfiles percona/percona-xtrabackup:8.0.34 /bin/bash -c "xtrabackup --copy-back --datadir=/xtrabackup_backupfiles/restored --target-dir=/xtrabackup_backupfiles"
```

### Options:

- `--copy-back`: Copies the backup files to the MySQL data directory.
- `--datadir`: Specifies the target data directory for MySQL.
- `--target-dir`: The directory where the prepared backup is stored.

## Final Notes

- Ensure that the permissions and ownership of the restored data directory are correctly set for MySQL.

```bash
chown -R 1001:1001 /xtrabackup_backupfiles/restored
```

- After restoration, verify the integrity and functionality of the database to confirm that everything has been restored successfully.
