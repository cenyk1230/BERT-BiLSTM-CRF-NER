bert-base-ner-train \
    -data_dir ./data_ner \
    -output_dir ./output_ner \
    -init_checkpoint ./albert_tiny/bert_model.ckpt \
    -bert_config_file ./albert_tiny/bert_config.json \
    -vocab_file ./albert_tiny/vocab.txt \
    -device_map 0 \
    -batch_size 16 \
    -num_train_epoch 5 \
