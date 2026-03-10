// =================================================================================================
//! @file string_run.c
//! @author STEER Framework Contributors
//! @brief This file implements the TestU01 String Run test (sstring_Run) for the STEER framework.
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

#define PROGRAM_NAME        "testu01_string_run_test"
#define PROGRAM_VERSION     "0.1.0"
#define TEST_NAME           "string run"
#define TEST_DESCRIPTION \
"The String Run test (sstring_Run) counts runs of consecutive identical bits (0-runs and \
1-runs) in the bitstream and compares the distribution of run lengths against the expected \
geometric distribution. Under the null hypothesis, the probability of a run of length k is \
(1/2)^k for k < maxLen and (1/2)^(maxLen-1) for k >= maxLen. A chi-squared test is applied \
to both 0-runs and 1-runs, then the statistics are combined. This test detects generators \
that produce too many or too few consecutive identical bits."
#define CONFIGURATION_COUNT         1
#define TESTU01_NAME                "TestU01 Crush Battery"

#define MINIMUM_BITSTREAM_COUNT     1
#define MINIMUM_BITSTREAM_LENGTH    8192
#define MINIMUM_SIGNIFICANCE_LEVEL  0.0
#define MAXIMUM_SIGNIFICANCE_LEVEL  1.0

#define SRUN_MAX_LENGTH_DEFAULT     8

// =================================================================================================
//  Private types
// =================================================================================================

typedef struct ttestu01_stringrunprivatedata
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
    uint64_t                    maxRunLength;
    double                      chiSquared;
    double                      probabilityValue;
}
tTestU01_StringRunPrivateData;

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
            "max run length",
            STEER_JSON_VALUE_UNSIGNED_64_BIT_INTEGER,
            NULL,
            NULL,
            "8",
            "4",
            "16"
        }
    }
};

static tSTEER_ParametersInfo gParametersInfo = {
    TEST_NAME,
    &gParameterInfoList
};

// =================================================================================================
//  RunTest
// =================================================================================================
int32_t RunTest(tTestU01_StringRunPrivateData* privateData,
                uint8_t* bitstreamBuffer,
                bool* passed)
{
    int32_t result = STEER_RESULT_SUCCESS;
    uint64_t maxLen = privateData->maxRunLength;
    uint64_t numCategories = maxLen;  // categories 1..maxLen-1 and >=maxLen
    uint64_t* observed0 = NULL;  // 0-run counts
    uint64_t* observed1 = NULL;  // 1-run counts
    uint64_t total0 = 0;
    uint64_t total1 = 0;
    double chiSq0 = 0.0, chiSq1 = 0.0;
    uint64_t n = privateData->bitstreamLength;
    uint64_t i;
    int runLength;
    uint8_t runBit;
    uint64_t df;

    // Allocate observed arrays
    result = STEER_AllocateMemory(numCategories * sizeof(uint64_t), (void**)&observed0);
    if (result != STEER_RESULT_SUCCESS) return result;

    result = STEER_AllocateMemory(numCategories * sizeof(uint64_t), (void**)&observed1);
    if (result != STEER_RESULT_SUCCESS)
    {
        STEER_FreeMemory((void**)&observed0);
        return result;
    }

    memset(observed0, 0, numCategories * sizeof(uint64_t));
    memset(observed1, 0, numCategories * sizeof(uint64_t));

    // Scan bitstream for runs
    runBit = bitstreamBuffer[0];
    runLength = 1;

    for (i = 1; i < n; i++)
    {
        if (bitstreamBuffer[i] == runBit)
        {
            runLength++;
        }
        else
        {
            // End of run — categorize
            int cat = (runLength >= (int)maxLen) ? (int)(numCategories - 1) : (runLength - 1);
            if (runBit == 0)
            {
                observed0[cat]++;
                total0++;
            }
            else
            {
                observed1[cat]++;
                total1++;
            }
            runBit = bitstreamBuffer[i];
            runLength = 1;
        }
    }
    // Final run
    {
        int cat = (runLength >= (int)maxLen) ? (int)(numCategories - 1) : (runLength - 1);
        if (runBit == 0)
        {
            observed0[cat]++;
            total0++;
        }
        else
        {
            observed1[cat]++;
            total1++;
        }
    }

    // Chi-squared for 0-runs
    // P(run length = k) = (1/2)^k for k = 1..maxLen-1
    // P(run length >= maxLen) = (1/2)^(maxLen-1)
    chiSq0 = 0.0;
    for (i = 0; i < numCategories - 1; i++)
    {
        double prob = pow(0.5, (double)(i + 1));
        double expected = (double)total0 * prob;
        if (expected > 0.0)
        {
            double diff = (double)observed0[i] - expected;
            chiSq0 += (diff * diff) / expected;
        }
    }
    {
        double prob = pow(0.5, (double)(maxLen - 1));
        double expected = (double)total0 * prob;
        if (expected > 0.0)
        {
            double diff = (double)observed0[numCategories - 1] - expected;
            chiSq0 += (diff * diff) / expected;
        }
    }

    // Chi-squared for 1-runs (same distribution)
    chiSq1 = 0.0;
    for (i = 0; i < numCategories - 1; i++)
    {
        double prob = pow(0.5, (double)(i + 1));
        double expected = (double)total1 * prob;
        if (expected > 0.0)
        {
            double diff = (double)observed1[i] - expected;
            chiSq1 += (diff * diff) / expected;
        }
    }
    {
        double prob = pow(0.5, (double)(maxLen - 1));
        double expected = (double)total1 * prob;
        if (expected > 0.0)
        {
            double diff = (double)observed1[numCategories - 1] - expected;
            chiSq1 += (diff * diff) / expected;
        }
    }

    privateData->chiSquared = chiSq0 + chiSq1;

    // Combined df = 2 * (numCategories - 1)
    df = 2 * (numCategories - 1);
    privateData->probabilityValue = cephes_igamc((double)df / 2.0,
                                                  privateData->chiSquared / 2.0);

    *passed = (privateData->probabilityValue >= privateData->significanceLevel);

    STEER_FreeMemory((void**)&observed0);
    STEER_FreeMemory((void**)&observed1);
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
    tTestU01_StringRunPrivateData* privData = NULL;

    *testPrivateData = NULL;
    *bufferSizeInBytes = 0;

    result = STEER_AllocateMemory(sizeof(tTestU01_StringRunPrivateData), (void**)&privData);

    if (result == STEER_RESULT_SUCCESS)
    {
        uint_fast32_t i = 0;
        void* nativeValue = NULL;

        privData->cliArguments = cliArguments;
        privData->maxRunLength = SRUN_MAX_LENGTH_DEFAULT;

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
            else if (strcmp(parameters->parameter[i].name, "max run length") == 0)
            {
                result = STEER_GetNativeValue(parameters->parameter[i].dataType,
                                              parameters->parameter[i].value, &nativeValue);
                if (result == STEER_RESULT_SUCCESS)
                {
                    privData->maxRunLength = *((uint64_t*)nativeValue);
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
    ((tTestU01_StringRunPrivateData*)testPrivateData)->report = report;
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
    tTestU01_StringRunPrivateData* privData = (tTestU01_StringRunPrivateData*)testPrivateData;
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
    tTestU01_StringRunPrivateData* privData = (tTestU01_StringRunPrivateData*)(*testPrivateData);

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
