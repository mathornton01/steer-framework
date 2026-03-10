// =================================================================================================
//! @file permutation.c
//! @author STEER Framework Contributors
//! @brief This file implements the TestU01 Permutation test (sknuth_Permutation) for the
//!        STEER framework.
//! @remarks Requires ANSI C99 (or better) compliant compilers.
//! @remarks Supported host operating systems: Any *nix
//! @copyright Copyright (c) 2024 Anametric, Inc. All rights reserved.
//!
//  Includes
// =================================================================================================
#include "steer.h"
#include "steer_json_utilities.h"
#include "steer_nist_sts_utilities_private.h"
#include "steer_parameters_info_utilities.h"
#include "steer_report_utilities.h"
#include "steer_report_utilities_private.h"
#include "steer_string_utilities.h"
#include "steer_string_utilities_private.h"
#include "steer_test_info_utilities.h"
#include "steer_test_shell.h"
#include "steer_utilities.h"
#include "steer_utilities_private.h"
#include "steer_value_utilities.h"
#include "cephes.h"
#include "defs.h"
#include <math.h>
#include <stdlib.h>
#include <string.h>

// =================================================================================================
//  Private constants
// =================================================================================================

#define PROGRAM_NAME        "testu01_permutation_test"
#define PROGRAM_VERSION     "0.1.0"
#define TEST_NAME           "permutation"
#define TEST_DESCRIPTION \
"The Permutation test (sknuth_Permutation) converts the bitstream to a sequence of uniform \
values and takes non-overlapping t-tuples. For each t-tuple, it determines the rank of the \
permutation formed by ordering the elements. The observed frequency of each permutation is \
compared to the expected uniform distribution using a chi-squared test. Under the null \
hypothesis of randomness, each of the t! permutations should be equally likely. This test \
detects dependencies in the ordering structure of consecutive generator outputs."
#define CONFIGURATION_COUNT         1
#define TESTU01_NAME                "TestU01 Crush Battery"

#define MINIMUM_BITSTREAM_COUNT     1
#define MINIMUM_BITSTREAM_LENGTH    8192
#define MINIMUM_SIGNIFICANCE_LEVEL  0.0
#define MAXIMUM_SIGNIFICANCE_LEVEL  1.0

// Permutation test parameters
#define PERM_BITS_PER_VALUE     32      // Bits per uniform value
#define PERM_T_DEFAULT          5       // Tuple size (t)

// =================================================================================================
//  Private types
// =================================================================================================

typedef struct ttestu01_permutationprivatedata
{
    tSTEER_CliArguments*        cliArguments;
    tSTEER_ReportPtr            report;
    uint64_t                    bitstreamCount;
    uint64_t                    bitstreamLength;
    double                      significanceLevel;
    uint32_t                    significanceLevelPrecision;
    uint64_t                    minimumTestCountRequiredForSignificance;
    uint64_t                    predictedPassedTestCount;
    uint64_t                    predictedFailedTestCount;
    tSTEER_ConfigurationState   configurationState[CONFIGURATION_COUNT];
    uint64_t                    ones;
    uint64_t                    zeros;
    double                      chiSquared;
    double                      probabilityValue;
    uint64_t                    tupleSize;
}
tTestU01_PermutationPrivateData;

// =================================================================================================
//  Private globals
// =================================================================================================

static tSTEER_InfoList gReferences = {
    1,
    {
        "P. L'Ecuyer and R. Simard, TestU01: A C Library for Empirical Testing of Random Number Generators, ACM TOMACS, 2007"
    }
};

static tSTEER_InfoList gAuthors = {
    2,
    {
        "Pierre L'Ecuyer",
        "Richard Simard"
    }
};

static tSTEER_InfoList gContributors = {
    1,
    {
        STEER_CONTRIBUTOR_GARY_WOODCOCK
    }
};

static tSTEER_InfoList gMaintainers = {
    2,
    {
        STEER_MAINTAINER_ANAMETRIC,
        STEER_MAINTAINER_SMU_DARWIN_DEASON
    }
};

static tSTEER_TestInfo gTestInfo = {
    TEST_NAME,
    TESTU01_NAME,
    TEST_DESCRIPTION,
    eSTEER_Complexity_Average,
    &gReferences,
    PROGRAM_NAME,
    PROGRAM_VERSION,
    eSTEER_InputFormat_Bitstream,
    STEER_REPOSITORY_URI,
    &gAuthors,
    &gContributors,
    &gMaintainers,
    STEER_CONTACT
};

static tSTEER_ParameterInfoList gParameterInfoList = {
    4,
    {
        {
            STEER_JSON_TAG_BITSTREAM_COUNT,
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            STEER_JSON_VALUE_BITSTREAMS,
            "1",
            "1",
            NULL
        },
        {
            STEER_JSON_TAG_BITSTREAM_LENGTH,
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            STEER_JSON_VALUE_BITS,
            "1000000",
            "8192",
            NULL
        },
        {
            STEER_JSON_TAG_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
            NULL,
            STEER_JSON_VALUE_DEFAULT_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_MINIMUM_SIGNIFICANCE_LEVEL,
            STEER_JSON_VALUE_MAXIMUM_SIGNIFICANCE_LEVEL
        },
        {
            "tuple size",
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            NULL,
            "5",
            "3",
            "7"
        }
    }
};

static tSTEER_ParametersInfo gParametersInfo = {
    TEST_NAME,
    &gParameterInfoList
};

// =================================================================================================
//  Helper: extract uniform [0,1) from bitstream
// =================================================================================================
static double ExtractUniform(uint8_t* buffer, uint64_t bitOffset)
{
    uint32_t value = 0;
    int i;
    for (i = 0; i < PERM_BITS_PER_VALUE; i++)
        value = (value << 1) | buffer[bitOffset + i];
    return (double)value / 4294967296.0;
}

// =================================================================================================
//  Helper: compute permutation rank using Lehmer code
// =================================================================================================
static uint32_t PermutationRank(double* values, int t)
{
    // Compute the Lehmer code and convert to a rank in [0, t!)
    uint32_t rank = 0;
    int i, j;

    // Precompute factorials (max t is 7, so 7 entries suffice)
    int factorials[8];
    factorials[0] = 1;
    for (i = 1; i < t; i++)
        factorials[i] = factorials[i - 1] * i;

    for (i = 0; i < t - 1; i++)
    {
        int count = 0;
        for (j = i + 1; j < t; j++)
        {
            if (values[j] < values[i])
                count++;
        }
        rank += count * factorials[t - 1 - i];
    }
    return rank;
}

// =================================================================================================
//  RunTest
// =================================================================================================
int32_t RunTest(tTestU01_PermutationPrivateData* privateData,
                uint8_t* bitstreamBuffer,
                bool* passed)
{
    int32_t result = STEER_RESULT_SUCCESS;
    uint64_t* observed = NULL;
    uint64_t numValues = 0;
    uint64_t numTuples = 0;
    double expected = 0.0;
    double chiSquared = 0.0;
    uint64_t i;
    uint64_t t = privateData->tupleSize;
    uint64_t permCategories = 1;
    uint64_t permDf;
    double* tuple = NULL;

    // Compute t!
    for (i = 2; i <= t; i++)
        permCategories *= i;
    permDf = permCategories - 1;

    // Dynamically allocate observed array and tuple array
    result = STEER_AllocateMemory(permCategories * sizeof(uint64_t), (void**)&observed);
    if (result != STEER_RESULT_SUCCESS) return result;

    result = STEER_AllocateMemory(t * sizeof(double), (void**)&tuple);
    if (result != STEER_RESULT_SUCCESS)
    {
        STEER_FreeMemory((void**)&observed);
        return result;
    }

    memset(observed, 0, permCategories * sizeof(uint64_t));

    // Number of uniform values we can extract
    numValues = privateData->bitstreamLength / PERM_BITS_PER_VALUE;
    // Number of non-overlapping t-tuples
    numTuples = numValues / t;

    if (numTuples < 1)
    {
        *passed = false;
        STEER_FreeMemory((void**)&observed);
        STEER_FreeMemory((void**)&tuple);
        return result;
    }

    // Count frequency of each permutation
    for (i = 0; i < numTuples; i++)
    {
        uint64_t j;
        uint32_t rank;

        for (j = 0; j < t; j++)
            tuple[j] = ExtractUniform(bitstreamBuffer,
                                      (i * t + j) * PERM_BITS_PER_VALUE);

        rank = PermutationRank(tuple, (int)t);
        if (rank < permCategories)
            observed[rank]++;
    }

    // Expected count per permutation
    expected = (double)numTuples / (double)permCategories;

    // Chi-squared statistic
    chiSquared = 0.0;
    for (i = 0; i < permCategories; i++)
    {
        double diff = (double)observed[i] - expected;
        chiSquared += (diff * diff) / expected;
    }

    privateData->chiSquared = chiSquared;

    // P-value via incomplete gamma
    privateData->probabilityValue = cephes_igamc((double)permDf / 2.0,
                                                  chiSquared / 2.0);

    *passed = (privateData->probabilityValue >= privateData->significanceLevel);

    STEER_FreeMemory((void**)&observed);
    STEER_FreeMemory((void**)&tuple);
    return result;
}

// =================================================================================================
//  GetTestInfo
// =================================================================================================
char* GetTestInfo(void)
{
    char* json = NULL;
    int32_t result = STEER_TestInfoToJson(&gTestInfo, &json);
    if (result == STEER_RESULT_SUCCESS)
        return json;
    else
        return NULL;
}

// =================================================================================================
//  GetParametersInfo
// =================================================================================================
char* GetParametersInfo(void)
{
    char* json = NULL;
    int32_t result = STEER_ParametersInfoToJson(&gParametersInfo, &json);
    if (result == STEER_RESULT_SUCCESS)
        return json;
    else
        return NULL;
}

// =================================================================================================
//  InitTest
// =================================================================================================
int32_t InitTest(tSTEER_CliArguments* cliArguments,
                 tSTEER_ParameterSet* parameters,
                 void** testPrivateData,
                 uint64_t* bufferSizeInBytes)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_PermutationPrivateData* privData = NULL;

    *testPrivateData = NULL;
    *bufferSizeInBytes = 0;

    result = STEER_AllocateMemory(sizeof(tTestU01_PermutationPrivateData), (void**)&privData);

    if (result == STEER_RESULT_SUCCESS)
    {
        uint_fast32_t i = 0;
        void* nativeValue = NULL;

        privData->cliArguments = cliArguments;
        privData->tupleSize = PERM_T_DEFAULT;

        for (i = 0; i < parameters->count; i++)
        {
            if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_BITSTREAM_COUNT) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->bitstreamCount = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_BITSTREAM_LENGTH) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->bitstreamLength = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            else if (strcmp(parameters->parameter[i].name, STEER_JSON_TAG_SIGNIFICANCE_LEVEL) == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->significanceLevel = *((double*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
                if (result == STEER_RESULT_SUCCESS)
                {
                    if (parameters->parameter[i].precision != NULL)
                        result = STEER_ConvertStringToUnsigned32BitInteger(
                            parameters->parameter[i].precision,
                            &(privData->significanceLevelPrecision));
                }
            }
            else if (strcmp(parameters->parameter[i].name, "tuple size") == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->tupleSize = *((uint64_t*)nativeValue);
                    STEER_FreeMemory(&nativeValue);
                }
            }
            if (result != STEER_RESULT_SUCCESS) break;
        }

        if ((privData->bitstreamCount < MINIMUM_BITSTREAM_COUNT) ||
            (privData->bitstreamLength < MINIMUM_BITSTREAM_LENGTH) ||
            ((privData->bitstreamLength % 8) != 0) ||
            (privData->significanceLevel <= MINIMUM_SIGNIFICANCE_LEVEL) ||
            (privData->significanceLevel >= MAXIMUM_SIGNIFICANCE_LEVEL))
        {
            result = STEER_CHECK_ERROR(EINVAL);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_GetMinimumTestCount(privData->significanceLevel,
                                               privData->bitstreamCount,
                                               &(privData->minimumTestCountRequiredForSignificance),
                                               &(privData->predictedPassedTestCount),
                                               &(privData->predictedFailedTestCount));
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            privData->configurationState[0].configurationId = 0;
            *testPrivateData = (void*)privData;
            *bufferSizeInBytes = privData->bitstreamLength / 8;
        }
    }

    if (result != STEER_RESULT_SUCCESS)
        STEER_FreeMemory((void**)&privData);
    return result;
}

// =================================================================================================
//  GetConfigurationCount
// =================================================================================================
uint32_t GetConfigurationCount(void* testPrivateData)
{
    return CONFIGURATION_COUNT;
}

// =================================================================================================
//  SetReport
// =================================================================================================
int32_t SetReport(void* testPrivateData, tSTEER_ReportPtr report)
{
    ((tTestU01_PermutationPrivateData*)testPrivateData)->report = report;
    return STEER_RESULT_SUCCESS;
}

// =================================================================================================
//  ExecuteTest
// =================================================================================================
int32_t ExecuteTest(void* testPrivateData,
                    const char* bitstreamId,
                    uint8_t* buffer,
                    uint64_t bufferSizeInBytes,
                    uint64_t bytesInBuffer,
                    uint64_t numZeros,
                    uint64_t numOnes)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_PermutationPrivateData* privData = (tTestU01_PermutationPrivateData*)testPrivateData;
    bool passed = false;
    char calculationStr[STEER_STRING_MAX_LENGTH] = { 0 };
    char criterionStr[STEER_STRING_MAX_LENGTH] = { 0 };
    uint64_t testId = 0;
    char* end = NULL;

    testId = strtoull(bitstreamId, &end, 0) - 1;

    privData->ones = numOnes;
    privData->zeros = numZeros;
    privData->configurationState[0].accumulatedOnes += numOnes;
    privData->configurationState[0].accumulatedZeros += numZeros;

    result = RunTest(privData, buffer, &passed);

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%" PRIu64 "", numOnes);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_ONES,
                                            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
                                            NULL, STEER_JSON_VALUE_BITS, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, "%" PRIu64 "", numZeros);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_ZEROS,
                                            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
                                            NULL, STEER_JSON_VALUE_BITS, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->chiSquared);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            "chi squared",
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(calculationStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(calculationStr, STEER_DEFAULT_FLOATING_POINT_STRING_FORMAT,
                STEER_DEFAULT_FLOATING_POINT_PRECISION, privData->probabilityValue);
        result = STEER_AddCalculationToTest(privData->report, 0, testId,
                                            STEER_JSON_TAG_PROBABILITY_VALUE,
                                            STEER_JSON_VALUE_DOUBLE_PRECISION_FLOATING_POINT,
                                            STEER_JSON_VALUE_DEFAULT_FLOATING_POINT_PRECISION,
                                            NULL, calculationStr);
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        memset(criterionStr, 0, STEER_STRING_MAX_LENGTH);
        sprintf(criterionStr, "%s of %.*f >= %s of %.*f",
                STEER_JSON_TAG_PROBABILITY_VALUE,
                STEER_DEFAULT_FLOATING_POINT_PRECISION,
                privData->probabilityValue,
                STEER_JSON_TAG_SIGNIFICANCE_LEVEL,
                privData->significanceLevelPrecision,
                privData->significanceLevel);
        result = STEER_AddCriterionToTest(privData->report, 0, testId, criterionStr,
                                          (privData->probabilityValue >= privData->significanceLevel));
    }

    if (result == STEER_RESULT_SUCCESS)
    {
        bool eval_passed = false;
        result = STEER_AddEvaluationToTest(privData->report, 0, testId, &eval_passed);
        if (result == STEER_RESULT_SUCCESS)
        {
            privData->configurationState[0].testsRun++;
            if (eval_passed)
                privData->configurationState[0].testsPassed++;
            else
                privData->configurationState[0].testsFailed++;
        }
    }

    STEER_FreeMemory((void**)&buffer);
    return result;
}

// =================================================================================================
//  FinalizeTest
// =================================================================================================
int32_t FinalizeTest(void** testPrivateData, uint64_t suppliedNumberOfBitstreams)
{
    int32_t result = STEER_RESULT_SUCCESS;
    tTestU01_PermutationPrivateData* privData = (tTestU01_PermutationPrivateData*)(*testPrivateData);

    if (privData != NULL)
    {
        double probabilityValueUniformity = 0.0;
        uint64_t proportionThresholdMinimum = 0;
        uint64_t proportionThresholdMaximum = 0;

        result = STEER_NistStsAddRequiredMetricsToConfiguration(privData->report, 0,
                    suppliedNumberOfBitstreams,
                    privData->minimumTestCountRequiredForSignificance,
                    privData->configurationState[0].testsPassed,
                    privData->predictedPassedTestCount,
                    privData->configurationState[0].accumulatedOnes,
                    privData->configurationState[0].accumulatedZeros);

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddMetricsToConfiguration(privData->report, 0, false,
                        suppliedNumberOfBitstreams, privData->significanceLevel,
                        &probabilityValueUniformity,
                        &proportionThresholdMinimum, &proportionThresholdMaximum);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_AddConfusionMatrixMetricsToConfiguration(privData->report, 0,
                        privData->minimumTestCountRequiredForSignificance,
                        privData->configurationState[0].testsRun,
                        privData->configurationState[0].testsPassed,
                        privData->configurationState[0].testsFailed,
                        privData->predictedPassedTestCount,
                        privData->predictedFailedTestCount);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddRequiredCriterionToConfiguration(privData->report, 0,
                        suppliedNumberOfBitstreams,
                        privData->configurationState[0].testsPassed,
                        privData->significanceLevel,
                        privData->significanceLevelPrecision,
                        privData->minimumTestCountRequiredForSignificance);
        }

        if (result == STEER_RESULT_SUCCESS)
        {
            result = STEER_NistStsAddCriteriaToConfiguration(privData->report, 0,
                        probabilityValueUniformity,
                        proportionThresholdMinimum, proportionThresholdMaximum,
                        privData->configurationState[0].testsRun,
                        privData->configurationState[0].testsPassed);
        }

        if (result == STEER_RESULT_SUCCESS)
            result = STEER_AddEvaluationToConfiguration(privData->report, 0);

        STEER_FreeMemory((void**)testPrivateData);
    }
    return result;
}

// =================================================================================================
//  main
// =================================================================================================
int main(int argc, const char* argv[])
{
    return STEER_Run(PROGRAM_NAME, argc, argv,
                     GetTestInfo, GetParametersInfo,
                     InitTest, GetConfigurationCount,
                     SetReport, ExecuteTest, FinalizeTest);
}

// =================================================================================================
