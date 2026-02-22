# Before You Proceed – Checklist

Use this checklist to confirm everything is in order before running the wooded area mapping pipeline.

## 1. VM cost lesson (done)

- **Previous VMs:** Old instances were left running by mistake and cost about **$20**. They have been **shut down and deleted**.
- **From now on:** Always **stop** the VM when you finish (`gcloud compute instances stop wooded-mapping-vm --zone=us-central1-a`) or **delete** it when the phase is done. Set billing alerts in [GCP Billing](https://console.cloud.google.com/billing).

## 2. Verify GCP project and account

Confirm you are using the **correct project** (and thus the right account/billing):

```powershell
gcloud config get-value project
```

**Expected (current setup):** `wooded-488021`  
Account: **mindisemptea@gmail.com**  
If you use a different project, set it with `gcloud config set project YOUR_PROJECT_ID` and use that project everywhere in the docs.

## 3. Verify GCS bucket

Confirm the **bucket** you use for data is the one you intend (e.g. new account/bucket):

```powershell
# List buckets in the current project
gcloud storage buckets list
# Or: gsutil ls

# Quick test: list something in your data bucket (adjust bucket name if different)
gsutil ls gs://ps4-woodedarea/
```

**Current bucket used in this repo:** `ps4-woodedarea`  
If your bucket has a different name, use your bucket name in all commands and scripts (e.g. `--bucket YOUR_BUCKET`).

## 4. Summary

| What              | Value |
|-------------------|--------|
| GCP project       | `wooded-488021` |
| GCS bucket        | `ps4-woodedarea` |
| Account           | `mindisemptea@gmail.com` |

| Check              | Command / action |
|--------------------|------------------|
| Active GCP project | `gcloud config get-value project` → expect `wooded-488021` |
| Active account    | `gcloud config get-value account` → expect `mindisemptea@gmail.com` |
| Bucket access     | `gsutil ls gs://ps4-woodedarea/` succeeds |
| VM habit          | Always stop or delete VMs when done; billing alerts set |

Once these match what you expect, you’re good to proceed with the project.
