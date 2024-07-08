cluster_label(){
    input_file="./text.jsonl"
    output_file="./test1.jsonl"
    text_key="content"
    start_idx="0"

    python main.py \
        --input_file $input_file \
        --output_file $output_file \
        --start_idx $start_idx \
        --sleep_time 10
}
cluster_label