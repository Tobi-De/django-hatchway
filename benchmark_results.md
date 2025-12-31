# Benchmark Results

## Metadata

- **framework**: django-hatchway
- **python_version**: 3.14.2 (main, Dec  9 2025, 19:03:28) [Clang 21.1.4 ]

## Results

| Name | Min (µs) | Max (µs) | Mean (µs) | Median (µs) | StdDev | OPS |
|------|----------|----------|-----------|-------------|--------|-----|
| test_post_list_empty | 295.93 | 639.42 | 338.00 | 334.18 | 26.16 | 2959 |
| test_post_list_small | 4768.16 | 5732.31 | 5057.42 | 5047.94 | 142.16 | 198 |
| test_post_list_medium | 5001.37 | 5699.33 | 5259.90 | 5241.94 | 127.46 | 190 |
| test_post_list_large | 5241.58 | 8358.41 | 5502.07 | 5447.67 | 277.77 | 182 |
| test_post_list_with_filters | 9332.60 | 16976.07 | 9967.47 | 9659.88 | 1176.11 | 100 |
| test_post_detail | 885.15 | 1459.86 | 954.30 | 947.28 | 47.00 | 1048 |
| test_post_detail_with_many_comments | 901.66 | 1129.78 | 963.41 | 955.52 | 39.58 | 1038 |
| test_post_create_simple | 892.09 | 1445.00 | 954.94 | 947.07 | 43.39 | 1047 |
| test_post_create_large_content | 1008.26 | 1894.41 | 1085.25 | 1073.05 | 71.67 | 921 |
| test_post_update | 1290.79 | 3709.53 | 1405.95 | 1377.56 | 168.30 | 711 |
| test_post_search_small | 573.61 | 2241.94 | 771.06 | 645.96 | 254.63 | 1297 |
| test_post_search_large | 1195.12 | 3474.58 | 1353.13 | 1286.01 | 255.05 | 739 |
| test_bulk_create_10 | 2118.91 | 2764.48 | 2346.40 | 2361.60 | 109.97 | 426 |
| test_bulk_create_50 | 9853.04 | 19630.94 | 10648.51 | 10221.45 | 1671.47 | 94 |
| test_post_comments_list | 1271.74 | 3058.98 | 1390.85 | 1364.02 | 208.02 | 719 |
| test_comment_create | 752.75 | 2894.42 | 834.03 | 804.01 | 204.32 | 1199 |
| test_simple_schema | 371.10 | 586.53 | 411.53 | 405.69 | 25.04 | 2430 |
| test_complex_schema | 384.05 | 1028.15 | 427.67 | 421.32 | 30.90 | 2338 |
| test_list_serialization | 20025.74 | 26463.67 | 20704.93 | 20417.70 | 1051.60 | 48 |
| test_full_stack_overhead | 907.54 | 2979.34 | 1029.45 | 976.88 | 214.40 | 971 |
| test_schema_response | 9087.10 | 16068.72 | 9907.70 | 9394.76 | 1509.93 | 101 |
| test_simple_query_params | 18.60 | 49.97 | 21.22 | 20.93 | 1.94 | 47134 |
| test_complex_query_params | 26.36 | 74.40 | 29.29 | 28.89 | 2.29 | 34139 |
| test_body_validation | 25.36 | 87.93 | 28.79 | 28.42 | 2.47 | 34735 |
| test_mixed_sources | 22.47 | 177.29 | 25.84 | 25.43 | 3.19 | 38695 |
| test_sources_for_input | 6.97 | 40.28 | 7.71 | 7.61 | 0.75 | 129636 |
| test_extract_signifier | 3.35 | 17.78 | 3.62 | 3.58 | 0.31 | 276356 |
| test_is_optional | 1.62 | 16.25 | 1.80 | 1.78 | 0.19 | 555122 |
| test_minimal_view_overhead | 12.05 | 40.27 | 14.08 | 13.97 | 1.23 | 71019 |
| test_no_validation_overhead | 14.71 | 340.45 | 21.72 | 17.50 | 13.08 | 46046 |
| test_validation_success | 21.42 | 164.53 | 24.82 | 24.31 | 3.51 | 40293 |
| test_validation_failure | 32.35 | 81.09 | 37.56 | 37.02 | 3.38 | 26622 |
| test_dict_response | 21.59 | 63.82 | 23.94 | 23.73 | 1.57 | 41769 |
| test_list_response | 260.07 | 374.87 | 271.42 | 268.24 | 10.20 | 3684 |
